#!/usr/bin/env python3
"""Propose buff priorities + subskills + superskill for a remix of N skills.

Inputs:
  --chosen-n   chosen_n.json from pick_n_eligible.py
  --audits     directory of per-skill audit JSON files (name = safe id)
  --out        remix_plan.json

The agent should refine this plan with marketplace judgment; this script gives a
deterministic scaffold so remix mode is scriptable and resumable.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def safe_id(sid: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "_", sid)[:120]


def skill_slug(sid: str) -> str:
    if "@" in sid:
        return sid.split("@", 1)[1]
    return sid.split("/")[-1]


def gap_severity_score(gaps: list[dict]) -> float:
    w = {"critical": 4.0, "high": 2.0, "medium": 1.0, "low": 0.3}
    return sum(w.get(str(g.get("severity", "medium")).lower(), 1.0) for g in gaps)


def load_audits(audits_dir: Path, ids: list[str]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for sid in ids:
        p = audits_dir / f"{safe_id(sid)}.json"
        if p.exists():
            out[sid] = json.loads(p.read_text(encoding="utf-8"))
        else:
            # try any file containing slug
            slug = skill_slug(sid)
            hits = list(audits_dir.glob(f"*{slug}*.json"))
            if hits:
                out[sid] = json.loads(hits[0].read_text(encoding="utf-8"))
            else:
                out[sid] = {"gaps": [], "stats": {}, "missing": True}
    return out


def propose_subskills(names: list[str], domain: str | None) -> list[dict]:
    """Heuristic subskill ideas from name tokens — agent must refine."""
    joined = " ".join(names).lower()
    ideas: list[dict] = []

    def add(name: str, job: str, pulls_from: list[str]):
        ideas.append(
            {
                "name": name,
                "job": job,
                "pulls_from": pulls_from,
                "kind": "subskill",
            }
        )

    # Generic glue that almost always helps a remix
    add(
        "handoff-pack",
        "Normalize inputs/outputs between member skills so the superskill can chain them without silent context loss.",
        names[:],
    )
    add(
        "verify-gate",
        "Independent check before any member skill claims done — shared false-done prevention.",
        names[:],
    )

    if any(t in joined for t in ("write", "novel", "story", "fiction", "chapter", "outline")):
        add(
            "continuity-bridge",
            "Carry canon/timeline/vocab across writing stages that the individual skills treat separately.",
            [n for n in names if any(x in n for x in ("story", "novel", "write", "memory", "context", "plan"))],
        )
    if any(t in joined for t in ("eval", "test", "verify", "audit", "score")):
        add(
            "metric-rollup",
            "Roll member-skill metrics into one card the superskill can gate on.",
            names[:],
        )
    if any(t in joined for t in ("research", "search", "fetch", "web")):
        add(
            "evidence-attach",
            "Attach sourced research snippets into downstream skill packs with provenance.",
            names[:],
        )
    if domain:
        add(
            f"{domain}-defaults",
            f"Domain defaults and non-triggers for {domain} so the remix does not misfire on adjacent senses.",
            names[:],
        )

    # Cap to 2–4 subskills
    return ideas[:4]


def propose_superskill(names: list[str], domain: str | None, fork_name: str | None) -> dict:
    base = fork_name or (
        f"{domain}-pipeline" if domain else "-".join(n.split("-")[0] for n in names[:3]) + "-pipeline"
    )
    base = re.sub(r"[^a-z0-9-]+", "-", base.lower()).strip("-") or "remix-pipeline"
    return {
        "name": base if base.endswith("-remix") or "pipeline" in base else f"{base}-remix",
        "kind": "superskill",
        "job": (
            "End-to-end orchestrator: pick the right buffed member skill (or subskill) per phase, "
            "pass handoff packs, run verify gates, and refuse to claim done until the rollup passes."
        ),
        "phases": [
            "intake + non-trigger guard",
            "route to buffed member / subskill",
            "handoff-pack normalize",
            "verify-gate",
            "metric rollup + done",
        ],
        "wires": names[:],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--chosen-n", type=Path, required=True)
    ap.add_argument("--audits", type=Path, required=True, help="Dir of per-skill audit JSON")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--domain", default=None)
    ap.add_argument("--name", default=None, help="Superskill / package name override")
    ap.add_argument("--forge-rounds", type=int, default=50)
    ap.add_argument(
        "--allow-missing-audits",
        action="store_true",
        help="Allow propose when some/all member audits are missing (scaffolding only)",
    )
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    from pathlib import Path as _Path
    import sys as _sys

    _sys.path.insert(0, str(_Path(__file__).resolve().parent))
    from forge_phases import FORGE_ROUNDS, PHASES, phases_doc

    if args.forge_rounds != FORGE_ROUNDS:
        # Keep CLI override but default plan is the fixed 50-round phase model
        pass

    chosen_payload = json.loads(args.chosen_n.read_text(encoding="utf-8"))
    members = chosen_payload.get("chosen") or []
    ids = [m.get("id") for m in members]
    audits = load_audits(args.audits, ids)

    missing_ids = [sid for sid in ids if audits.get(sid, {}).get("missing")]
    if missing_ids and not args.allow_missing_audits:
        fail = {
            "decision": "FAIL",
            "error": "audits_incomplete",
            "message": (
                f"{len(missing_ids)}/{len(ids)} member audits missing under {args.audits} — "
                "finish R3 audit_incumbent before propose_remix (or pass --allow-missing-audits)"
            ),
            "missing_ids": missing_ids,
            "audits_dir": str(args.audits),
            "hint": "python3 scripts/audit_incumbent.py --skill-dir … --out discovery/audits/<safe_id>.json",
        }
        print(json.dumps(fail, indent=2))
        return 2

    # Buff priorities still scored from gaps (work happens inside P1–P2)
    scored = []
    for m in members:
        sid = m["id"]
        gaps = audits.get(sid, {}).get("gaps") or []
        score = gap_severity_score(gaps)
        scored.append(
            {
                "id": sid,
                "skill": skill_slug(sid),
                "installs_approx": m.get("installs_approx", m.get("installs")),
                "gap_score": score,
                "gap_ids": [g.get("id") for g in gaps],
                "audit_missing": bool(audits.get(sid, {}).get("missing")),
            }
        )
    scored.sort(key=lambda x: (-x["gap_score"], str(x["id"])))

    n = len(scored)
    buffs = []
    for s in scored:
        priority = "heavy" if s["gap_score"] >= 4 else ("medium" if s["gap_score"] >= 2 else "light")
        buffs.append(
            {
                **s,
                "priority": priority,
                "forge_rounds": 0,  # work is scheduled by fixed phases, not per-member round budgets
                "why_buff": (
                    f"gap_score={s['gap_score']}; gaps={s['gap_ids'][:6]} — "
                    "address during P1-unify / P2-enhance so the member carries its phase without false-done."
                ),
                "how_buff": (
                    "During P1 wire this member into the shared handoff/verify whole; "
                    "during P2 deepen the ability it uniquely contributes — not cosmetic README polish."
                ),
            }
        )

    names = [skill_slug(i) for i in ids]
    superskill = propose_superskill(names, args.domain, args.name)

    from manifold_engine import build_skill_manifold, render_manifold_md
    from wiring_compiler import compile_wiring, render_wiring_md

    manifold_atlas = build_skill_manifold(
        members,
        audits,
        domain=args.domain,
        skill_name=superskill["name"],
    )
    wiring_graph = compile_wiring(
        members,
        audits,
        domain=args.domain,
        package_name=superskill["name"],
    )
    # Merge algebraic synthesized subskills (typed guard, manifold projector, handoff, pullback, dominator gate)
    subskills = wiring_graph.get("synthesized_subskills") or propose_subskills(names, args.domain)

    # Fixed phase round map (replaces T1–T5 and per-member round slicing)
    round_map = []
    for p in PHASES:
        target = superskill["name"]
        if p["kind"] == "unify":
            target = "package-wholeness"
        elif p["kind"] == "enhance":
            target = "enhanced-abilities"
        elif p["kind"] == "metrics":
            target = "METRICS.md"
        elif p["kind"] == "awesome":
            target = "AWESOME_PROOF.md"
        round_map.append(
            {
                "kind": p["kind"],
                "phase_id": p["id"],
                "target": target,
                "rounds": list(p["rounds"]),
                "job": p["job"],
            }
        )

    all_gaps = []
    for m in members:
        all_gaps.extend(audits.get(m["id"], {}).get("gaps") or [])
    phase_doc = phases_doc(all_gaps)

    plan = {
        "mode": "remix",
        "n": n,
        "domain": args.domain,
        "members": members,
        "buffs": buffs,
        "subskills": subskills,
        "superskill": superskill,
        "forge_rounds": FORGE_ROUNDS,
        "phases": phase_doc["phases"],
        "round_map": round_map,
        "thesis": (
            "Span the underlying Lawvere-Amari generative skill manifold across complementary landmark "
            "skills, anti-unify conflicting clauses into chart coordinates, enforce Cech sheaf gluing, "
            "then forge on the fixed 50-round phase plan: P1 unify (more than sum of parts) → "
            "P2 enhance → P3 undeniable reproducible metrics (fix when not best) → "
            "P4 awesome proof (real novel / ≥99%-confident third-party bug find)."
        ),
        "agent_must_refine": [
            "Replace heuristic subskills with ones that match real member I/O after clone/read",
            "Drop a member from buff list only if it is already composition-ready (rare)",
            "Name the superskill for the user-facing end-to-end job, not a mashup of repo names",
            "Cite each upstream id in UPSTREAM.md / REMIX_PLAN.md",
            "Rounds 1–10 MUST be kind=unify and drive unify_wholeness toward PASS",
            "Rounds 21–25 MUST produce METRICS.md with reproducible commands; fix when not best",
            "Rounds 45–50 MUST produce AWESOME_PROOF.md with a real artifact or third-party bug URL",
            "Do not ship until unify_wholeness + phase checks + ship_check PASS",
        ],
        "audits_missing": missing_ids,
        "audits_complete": len(missing_ids) == 0,
        "manifold_summary": wiring_graph.get("manifold_theory"),
        "wiring_graph": wiring_graph,
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    wiring_out = args.out.parent / "wiring_graph.json"
    wiring_out.write_text(json.dumps(wiring_graph, indent=2) + "\n", encoding="utf-8")
    (args.out.parent / "WIRING_CONTRACT.md").write_text(
        render_wiring_md(wiring_graph), encoding="utf-8"
    )
    (args.out.parent / "manifold_atlas.json").write_text(
        json.dumps(manifold_atlas, indent=2) + "\n", encoding="utf-8"
    )
    (args.out.parent / "MANIFOLD_ATLAS.md").write_text(
        render_manifold_md(manifold_atlas), encoding="utf-8"
    )
    # Also write a markdown digest beside it
    md = args.out.with_suffix(".md")
    lines = [
        f"# Remix plan ({n} skills)",
        "",
        plan["thesis"],
        "",
        "## Members",
        "",
    ]
    for m in members:
        lines.append(f"- `{m.get('id')}` (installs≈{m.get('installs_approx', m.get('installs'))})")
    lines += ["", "## Buff priorities", ""]
    for b in buffs:
        lines.append(
            f"- **{b['priority']}** `{b['id']}` — {b['why_buff']}"
        )
    lines += ["", "## Subskills", ""]
    for s in subskills:
        lines.append(f"- `{s['name']}` — {s['job']}")
    lines += [
        "",
        "## Superskill",
        "",
        f"- `{superskill['name']}` — {superskill['job']}",
        "",
        "## Forge phases (fixed 50 rounds)",
        "",
    ]
    for rm in round_map:
        lines.append(
            f"- **{rm['kind']}** `{rm.get('phase_id', '')}` `{rm['target']}` → rounds {rm['rounds'][0]}–{rm['rounds'][1]}"
        )
    if missing_ids:
        lines += [
            "",
            "## Warnings",
            "",
            f"- Missing audits for: {', '.join(f'`{i}`' for i in missing_ids)}",
        ]
    md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    decision = "PASS_WITH_WARNINGS" if missing_ids else "PASS"
    out = {
        "decision": decision,
        "out": str(args.out),
        "md": str(md),
        "superskill": superskill["name"],
        "n_buffs": n,
        "audits_missing": missing_ids,
        "audits_complete": len(missing_ids) == 0,
    }
    if missing_ids:
        out["warnings"] = [
            {
                "code": "audits_incomplete",
                "missing_ids": missing_ids,
                "message": "plan scaffolded without full R3 audits — refine buffs after audit_incumbent",
            }
        ]
    print(json.dumps(out if args.json else plan, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
