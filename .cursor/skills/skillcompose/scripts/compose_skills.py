#!/usr/bin/env python3
"""Mechanical Lawvere-Amari & Kleisli Skill Composer for /skillcompose.

Takes a candidate pool (JSONL/JSON with materialized `local_dir` or `--upstreams-root`), runs:
  1. Submodular Noisy-OR + Fisher Log-Det Volume + JSD/NCD selection (with Nemhauser-Wolsey certificate)
  2. Static capability/script auditing (`audit_incumbent.py`)
  3. Lawvere-Amari Generative Manifold synthesis (`manifold_engine.py`: Fisher-Rao tangent basis,
     Galois conormal invariants, Plotkin-Reynolds anti-unified chart variables, Cech sheaf nerve)
  4. Algebraic Kleisli wiring compilation (`wiring_compiler.py`)
  5. Parnas-encapsulated composite package synthesis (`SKILL.md`, `references/MANIFOLD_ATLAS.md`,
     `references/members/*.md`, standalone `scripts/project_manifold.py`, and read-only sheaf +
     separation-logic gate `scripts/verify_dominator_gate.py`)
  6. Post-materialization static theorem verification (all 6 algebraic, geometric, & sheaf laws).
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from manifold_engine import (  # noqa: E402
    build_skill_manifold,
    evaluate_generalization_over_union,
    render_manifold_md,
)
from submodular_select import build_selection_report, role_posterior  # noqa: E402
from wiring_compiler import compile_wiring, render_wiring_md, slug_of, verify_graph  # noqa: E402

PROJECT_MANIFOLD_SCRIPT = """#!/usr/bin/env python3
\"\"\"Standalone Lawvere-Amari Inverse Chart Encoder & e-Geodesic Synthesizer (/skillcompose).

Maps a task input x in X onto the compiled skill manifold M:
  1. Conormal Domain Guard P_M(x): halts with exit 2 (`ABSTAIN_OFF_MANIFOLD`) on alien/polysemic inputs.
  2. Fisher-Rao Tangent Projection: computes chart coordinates theta*(x) and e-geodesic landmark weights.
  3. Anti-Unified Lawvere Fiber Resolution: instantiates contradiction-free clauses T_M(theta*(x)).
  4. Conditional Markov Kernel K_{theta*(x)}(y | x): evaluates exact probabilities over the 648-state
     structured output lattice Y and emits the MAP structured output + sheaf gluing obligations.
\"\"\"
from __future__ import annotations

import argparse
import itertools
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

AXIS_LEXICONS = {
    "spec_modality": {
        "json_contract": {"json", "schema", "schemas", "openapi", "contract", "contracts", "typed", "types", "interface", "payload", "manifest", "validation"},
        "formal_grammar_adr": {"rfc", "adr", "ebnf", "grammar", "formal", "precondition", "preconditions", "specification", "invariant", "invariants", "dsl", "protocol", "spec"},
        "informal_prose": {"brainstorm", "ideate", "freeform", "creative", "chat"},
    },
    "execution_regime": {
        "streaming_incremental": {"stream", "streaming", "incremental", "chunk", "chunked", "jsonl", "iterator", "cursor", "pipeline", "event", "webhook", "realtime"},
        "transactional_staged": {"transaction", "transactional", "migration", "staged", "atomic", "two", "phase", "commit", "zero", "downtime", "database", "sql", "sqlite"},
        "single_shot": {"single", "oneshot", "template", "snippet", "quick", "draft"},
    },
    "verification_channel": {
        "static_ast_contract": {"ast", "lint", "typecheck", "static", "syntax", "parse", "parser", "check", "structure", "kleene", "citation", "provenance"},
        "exogenous_exec_oracle": {"pytest", "jest", "test", "testing", "harness", "benchmark", "run", "execute", "sandbox", "empirical", "reproducible", "eval", "evals", "query", "verify"},
        "adversarial_differential": {"adversarial", "redteam", "exploit", "fuzz", "differential", "property", "counterexample", "security", "vulnerability", "audit", "critic", "critique"},
        "prose_self_check": {"polish", "review", "clean", "readability"},
    },
    "failure_semantics": {
        "abstain_exit2": {"abstain", "refuse", "refusal", "guard", "exit", "reject", "strict", "gate", "preflight"},
        "idempotent_rollback": {"rollback", "recovery", "checkpoint", "resume", "idempotent", "undo", "backup", "restore", "continuity", "ledger", "state"},
        "silent_partial": {"best", "effort", "fallback"},
    },
    "gluing_topology": {
        "sheaf_global_section": {"pullback", "sheaf", "reconcile", "bijective", "global", "consistency", "coherence", "canon", "cross", "ledger", "invariant"},
        "pairwise_handoff": {"handoff", "bridge", "adapter", "pack", "pipe", "chain", "stage", "wire"},
        "unlinked_outputs": {"standalone", "isolated"},
    },
    "context_disclosure": {
        "progressive_parnas": {"references", "scripts", "subskills", "modular", "encapsulate", "progressive", "disclosure", "compact"},
        "monolithic_prompt": {"mega", "all", "prompt"},
    },
}


def tokenize(text: str) -> list[str]:
    return [t for t in re.split(r"[^a-z0-9]+", (text or "").lower()) if len(t) >= 2]


def encode_x(text: str) -> dict[str, float]:
    toks = Counter(tokenize(text))
    sc = sum(toks[w] for w in ("stream", "streaming", "large", "million", "jsonl", "chunk", "incremental", "realtime", "batch"))
    st = sum(toks[w] for w in ("migration", "rollback", "state", "checkpoint", "database", "sql", "sqlite", "transaction", "zero", "downtime", "canon", "continuity"))
    sr = sum(toks[w] for w in ("rfc", "formal", "grammar", "strict", "security", "audit", "exploit", "contract", "schema", "invariant", "adversarial"))
    mv = sum(toks[w] for w in ("api", "schema", "reconcile", "pullback", "sheaf", "cross", "pipeline", "multi", "sync", "bridge"))
    return {
        "scale": round(1.0 - math.exp(-0.55 * sc), 4),
        "stateful": round(1.0 - math.exp(-0.55 * st), 4),
        "strict": round(1.0 - math.exp(-0.45 * sr), 4),
        "multi_view": round(1.0 - math.exp(-0.55 * mv), 4),
    }


def psi_xy(x_feat: dict[str, float], y: tuple[str, ...]) -> list[float]:
    spec, ex, ver, fail, glue, disc = y
    f0 = 1.0 if spec == "json_contract" else 0.0
    f1 = 1.0 if spec == "formal_grammar_adr" else 0.0
    f2 = 1.0 if ex == "streaming_incremental" else 0.0
    f3 = 1.0 if ex == "transactional_staged" else 0.0
    f4 = 1.0 if ver == "static_ast_contract" else 0.0
    f5 = 1.0 if ver == "exogenous_exec_oracle" else 0.0
    f6 = 1.0 if ver == "adversarial_differential" else 0.0
    f7 = 1.0 if fail == "abstain_exit2" else 0.0
    f8 = 1.0 if fail == "idempotent_rollback" else 0.0
    f9 = 1.0 if glue == "pairwise_handoff" else 0.0
    f10 = 1.0 if glue == "sheaf_global_section" else 0.0
    f11 = 1.0 if disc == "progressive_parnas" else 0.0
    return [
        f0, f1, f2, f3, f4, f5, f6, f7, f8, f9, f10, f11,
        x_feat["scale"] * f2,
        x_feat["stateful"] * (0.5 * f3 + 0.5 * f8),
        x_feat["strict"] * (0.5 * f1 + 0.5 * f6),
        x_feat["multi_view"] * f10,
    ]


def probe_eta(text: str, x_feat: dict[str, float]) -> list[float]:
    toks = Counter(tokenize(text))
    def lp(ax: str, val: str, base: float) -> float:
        hits = sum(toks[w] for w in AXIS_LEXICONS[ax].get(val, set()) if w in toks)
        return base + 0.55 * math.log1p(hits) + (1.15 if hits >= 2 else 0.0)
    return [
        lp("spec_modality", "json_contract", 0.2),
        lp("spec_modality", "formal_grammar_adr", 0.2),
        lp("execution_regime", "streaming_incremental", 0.0),
        lp("execution_regime", "transactional_staged", 0.0),
        lp("verification_channel", "static_ast_contract", 0.2),
        lp("verification_channel", "exogenous_exec_oracle", 0.35),
        lp("verification_channel", "adversarial_differential", 0.25),
        lp("failure_semantics", "abstain_exit2", 0.3),
        lp("failure_semantics", "idempotent_rollback", 0.15),
        lp("gluing_topology", "pairwise_handoff", 0.2),
        lp("gluing_topology", "sheaf_global_section", 0.25),
        lp("context_disclosure", "progressive_parnas", 0.35),
        1.1 * x_feat["scale"],
        1.1 * x_feat["stateful"],
        1.1 * x_feat["strict"],
        1.1 * x_feat["multi_view"],
    ]


def main() -> int:
    default_atlas = Path(__file__).resolve().parent.parent / "references" / "manifold_atlas.json"
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--atlas", type=Path, default=default_atlas)
    ap.add_argument("--input", required=True, help="Task prompt string or path to task file")
    ap.add_argument("--require", action="append", default=[], help="Optional axis=value override")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    atlas = json.loads(args.atlas.read_text(encoding="utf-8"))
    inp = Path(args.input)
    text = inp.read_text(encoding="utf-8", errors="replace") if inp.is_file() else args.input
    toks = set(tokenize(text))
    guard = atlas.get("domain_guard") or {}
    q_seed = set(tokenize(str(atlas.get("query") or "")))
    traps = (set(guard.get("polysemy_traps") or []) | set(guard.get("alien_tokens") or [])) - q_seed
    off_dom = set(guard.get("off_domain_tokens") or []) - q_seed
    dom_toks = set(guard.get("domain_tokens") or [])

    trap_hits = sorted(toks & traps)
    off_hits = sorted(toks & off_dom)
    if trap_hits or (off_hits and not (toks & dom_toks)):
        rep = {
            "ok": False,
            "decision": "ABSTAIN_OFF_MANIFOLD",
            "domain": atlas.get("domain"),
            "reasons": [f"conormal_domain_guard_rejected: trap_hits={trap_hits}, off_domain_hits={off_hits}"],
        }
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(json.dumps(rep, indent=2) + "\\n", encoding="utf-8")
        print(json.dumps(rep, indent=2))
        return 2

    x_feat = encode_x(text)
    geom = atlas["geometry"]
    eta_0 = geom["barycenter_eta"]
    g_half = geom["fisher_sqrt"]
    w_basis = geom["whitened_basis"]
    t_basis = geom["tangent_basis_eta"]
    p_eta = probe_eta(text, x_feat)
    raw_d = [p_eta[i] - eta_0[i] for i in range(len(eta_0))]
    w_d = [sum(g_half[r][c] * raw_d[c] for c in range(len(eta_0))) for r in range(len(eta_0))]
    theta = [sum(u[i] * w_d[i] for i in range(len(eta_0))) for u in w_basis]
    norm_t = math.sqrt(sum(c * c for c in theta))
    if norm_t > 3.0:
        theta = [c * 3.0 / norm_t for c in theta]
    eta_star = [eta_0[d] + sum(c * v[d] for c, v in zip(theta, t_basis)) for d in range(len(eta_0))]

    landmarks = atlas.get("landmarks") or []
    lm_weights = {}
    if landmarks:
        nd = []
        for lm in landmarks:
            lc = lm.get("chart_coordinates") or []
            sq = sum((a - b) ** 2 for a, b in zip(theta, lc))
            aff = lm.get("input_affinity") or {}
            asim = sum(x_feat[k] * float(aff.get(k, 0.0)) for k in x_feat)
            nd.append(-0.85 * sq + 1.25 * asim)
        mx = max(nd)
        exps = [math.exp(v - mx) for v in nd]
        zw = sum(exps)
        for lm, ew in zip(landmarks, exps):
            lm_weights[lm["slug"]] = round(ew / zw, 4)

    reqs = {}
    for item in args.require:
        if "=" in item:
            k, v = item.split("=", 1)
            reqs[k.strip()] = v.strip()

    logic = atlas["logic"]
    fiber = {ax: list(vals) for ax, vals in logic["conormal_core"].items()}
    chart_assign = {}
    tok_counts = Counter(tokenize(text))
    for ax, cv in (logic.get("chart_variables") or {}).items():
        dvals = list(cv["domain"])
        if ax in reqs and reqs[ax] in dvals:
            picked = [reqs[ax]]
        else:
            scored = [(sum(tok_counts[w] for w in AXIS_LEXICONS[ax].get(v, set()) if w in tok_counts), v) for v in dvals]
            bs = max(s for s, _ in scored)
            picked = [v for s, v in scored if s == bs] if bs > 0 else dvals
        fiber[ax] = picked
        chart_assign[ax] = picked

    axes_order = list(atlas["output_axes"].keys())
    space = list(itertools.product(*(atlas["output_axes"][a] for a in axes_order)))
    valid = []
    max_s = float("-inf")
    for idx, y in enumerate(space):
        if all(y[j] in fiber[axes_order[j]] for j in range(len(axes_order))):
            sc = sum(eta_star[d] * psi_xy(x_feat, y)[d] for d in range(len(eta_star)))
            valid.append((idx, sc))
            if sc > max_s:
                max_s = sc
    z = sum(math.exp(sc - max_s) for _, sc in valid)
    log_z = max_s + math.log(z)
    ranked = sorted(((math.exp(sc - log_z), idx) for idx, sc in valid), reverse=True)

    rep = {
        "ok": True,
        "decision": "SYNTHESIZE_ON_MANIFOLD",
        "domain": atlas.get("domain"),
        "fisher_chart_coordinates": [round(c, 5) for c in theta],
        "landmark_e_geodesic_weights": lm_weights,
        "resolved_lawvere_fiber": fiber,
        "resolved_chart_variables": chart_assign,
        "admissible_output_fiber_cardinality": len(valid),
        "map_structured_output": {axes_order[j]: space[ranked[0][1]][j] for j in range(len(axes_order))} if ranked else {},
        "sheaf_gluing_obligations": atlas["sheaf_nerve"]["overlaps"],
    }
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(rep, indent=2) + "\\n", encoding="utf-8")
    print(json.dumps(rep, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""

DOMINATOR_GATE_SCRIPT = """#!/usr/bin/env python3
\"\"\"Auto-generated Read-Only Post-Dominator, Sheaf Gluing & Separation-Logic Gate (/skillcompose).

Mechanically enforces:
  1. Exogenous Grounding (DPI escape): executes deterministic verification commands and checks exit == 0.
  2. Orthogonal Critic Non-Interference (W(gate) == empty): snapshots SHA-256 digests of protected
     deliverables BEFORE running checks and fails (exit 2) if any check mutates a deliverable.
  3. Sufficient-Statistic & Manifold Section Check: validates JSON contract and optional projected
     manifold section (`SYNTHESIZE_ON_MANIFOLD`, non-empty admissible fiber).
  4. Cech Sheaf 0-Coboundary Check (`--glue left.json:right.json:key1,key2`): deterministically verifies
     exact restriction agreement rho_u(y_u) == rho_v(y_v) across overlapping structured outputs.
\"\"\"
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def snapshot_files(paths: list[str]) -> dict[str, str | None]:
    out: dict[str, str | None] = {}
    for raw in paths:
        p = Path(raw)
        out[raw] = sha256_file(p) if p.is_file() else None
    return out


def check_sheaf_gluing(specs: list[str]) -> tuple[list[str], list[dict]]:
    reasons: list[str] = []
    checked: list[dict] = []
    for spec in specs:
        parts = spec.split(":", 2)
        if len(parts) != 3:
            reasons.append(f"invalid_glue_spec(expected left:right:k1,k2):{spec}")
            continue
        left_p, right_p, raw_keys = Path(parts[0]), Path(parts[1]), [k.strip() for k in parts[2].split(",") if k.strip()]
        if not left_p.is_file() or not right_p.is_file():
            reasons.append(f"missing_sheaf_view_file:{left_p}:{right_p}")
            continue
        try:
            left_doc = json.loads(left_p.read_text(encoding="utf-8"))
            right_doc = json.loads(right_p.read_text(encoding="utf-8"))
        except Exception as exc:
            reasons.append(f"invalid_sheaf_json:{exc}")
            continue
        mismatches = []
        for k in raw_keys:
            if k not in left_doc or k not in right_doc:
                mismatches.append({"key": k, "error": "missing_restriction_key"})
            elif left_doc[k] != right_doc[k]:
                mismatches.append({"key": k, "left": left_doc[k], "right": right_doc[k]})
        checked.append({"left": str(left_p), "right": str(right_p), "keys": raw_keys, "coboundary_zero": len(mismatches) == 0})
        if mismatches:
            reasons.append(f"sheaf_coboundary_defect({left_p.name}<->{right_p.name}):{mismatches}")
    return reasons, checked


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--protect", action="append", default=[], help="Deliverable path that must exist and remain unmutated")
    ap.add_argument("--contract", type=Path, default=None, help="Optional JSON sufficient-statistic contract to validate")
    ap.add_argument("--manifold-section", type=Path, default=None, help="Optional projected manifold section JSON to validate")
    ap.add_argument("--glue", action="append", default=[], help="Optional Cech sheaf overlap check left.json:right.json:key1,key2")
    ap.add_argument("--cmd", action="append", default=[], help="Exogenous verification shell command (repeatable)")
    args = ap.parse_args()

    reasons: list[str] = []
    for req in args.protect:
        if not Path(req).exists():
            reasons.append(f"missing_protected_deliverable:{req}")

    if args.contract is not None:
        if not args.contract.is_file():
            reasons.append(f"missing_contract:{args.contract}")
        else:
            try:
                data = json.loads(args.contract.read_text(encoding="utf-8"))
                if not data:
                    reasons.append("empty_contract_json")
            except Exception as exc:
                reasons.append(f"invalid_contract_json:{exc}")

    if args.manifold_section is not None:
        if not args.manifold_section.is_file():
            reasons.append(f"missing_manifold_section:{args.manifold_section}")
        else:
            try:
                ms = json.loads(args.manifold_section.read_text(encoding="utf-8"))
                if ms.get("decision") != "SYNTHESIZE_ON_MANIFOLD" or int(ms.get("admissible_output_fiber_cardinality") or 0) <= 0:
                    reasons.append(f"invalid_or_abstained_manifold_section:{ms.get('decision')}")
            except Exception as exc:
                reasons.append(f"invalid_manifold_section_json:{exc}")

    glue_reasons, glue_traces = check_sheaf_gluing(args.glue)
    reasons.extend(glue_reasons)

    before = snapshot_files(args.protect)
    cmd_traces = []
    for c in args.cmd:
        proc = subprocess.run(c, shell=True, capture_output=True, text=True)
        cmd_traces.append(
            {
                "cmd": c,
                "returncode": proc.returncode,
                "stdout_tail": proc.stdout[-600:],
                "stderr_tail": proc.stderr[-600:],
            }
        )
        if proc.returncode != 0:
            reasons.append(f"exogenous_oracle_failed(rc={proc.returncode}):{c}")

    after = snapshot_files(args.protect)
    mutated = [k for k in before if before[k] != after[k]]
    if mutated:
        reasons.append(f"separation_logic_violation_critic_mutated_targets:{mutated}")

    decision = "PASS" if not reasons else "FAIL"
    report = {
        "decision": decision,
        "protected_count": len(args.protect),
        "sheaf_overlaps_checked": len(glue_traces),
        "sheaf_coboundary_clean": len(glue_reasons) == 0,
        "exogenous_commands_run": len(cmd_traces),
        "separation_logic_clean": len(mutated) == 0,
        "reasons": reasons,
        "sheaf_traces": glue_traces,
        "traces": cmd_traces,
    }
    print(json.dumps(report, indent=2))
    return 0 if decision == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
"""

STAGE_PRIORITY = {
    "spec_grounding": 1,
    "static_contract": 2,
    "synthesis": 3,
    "state_recovery": 4,
    "exec_observation": 5,
    "adversarial_verify": 6,
}


def strip_frontmatter(md_text: str) -> str:
    if md_text.startswith("---"):
        parts = md_text.split("---", 2)
        if len(parts) == 3:
            return parts[2].strip()
    return md_text.strip()


def compose_package(
    candidates_path: Path,
    *,
    n: int,
    domain: str,
    query: str,
    out_dir: Path,
    skill_name: str = "domain-pack",
    upstreams_root: Path | None = None,
    seed: str = "skillcompose",
) -> dict[str, Any]:
    raw = candidates_path.read_text(encoding="utf-8").strip()
    rows: list[dict[str, Any]] = (
        json.loads(raw)
        if raw.startswith("[")
        else [json.loads(ln) for ln in raw.splitlines() if ln.strip()]
    )
    if upstreams_root is not None:
        for r in rows:
            if not r.get("local_dir"):
                cand_dir = upstreams_root / slug_of(str(r.get("id") or ""))
                if cand_dir.is_dir():
                    r["local_dir"] = str(cand_dir)

    eligible = [r for r in rows if r.get("eligible") is True]
    if not eligible:
        raise ValueError("No eligible candidates in pool")

    sel_report = build_selection_report(eligible, n, domain=domain, query=query, seed=seed)
    chosen = sel_report["chosen"]

    audits: dict[str, dict[str, Any]] = {}
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        for m in chosen:
            sid = str(m.get("id") or "")
            slug = slug_of(sid)
            ldir = Path(str(m.get("local_dir") or ""))
            if ldir.is_dir():
                audit_out = td_path / f"{slug}.json"
                subprocess.run(
                    [sys.executable, str(HERE / "audit_incumbent.py"), "--skill-dir", str(ldir), "--out", str(audit_out)],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                audits[sid] = json.loads(audit_out.read_text(encoding="utf-8"))

    # Order members along Kleisli causal flow
    def member_sort_key(m: dict[str, Any]) -> tuple[int, str]:
        rp = m.get("role_posterior") or role_posterior(m)
        top_role = max(rp.items(), key=lambda kv: kv[1])[0]
        return (STAGE_PRIORITY.get(top_role, 3), str(m.get("id") or ""))

    ordered_members = sorted(chosen, key=member_sort_key)
    manifold_atlas = build_skill_manifold(
        ordered_members,
        audits=audits,
        domain=domain,
        query=query,
        skill_name=skill_name,
    )
    gen_proof = evaluate_generalization_over_union(manifold_atlas)
    graph = compile_wiring(ordered_members, audits, domain=domain, package_name=skill_name)

    if out_dir.exists():
        shutil.rmtree(out_dir)
    (out_dir / "references" / "members").mkdir(parents=True, exist_ok=True)
    (out_dir / "scripts").mkdir(parents=True, exist_ok=True)

    # Write auto-generated Manifold Projector & Read-Only Post-Dominator / Sheaf Gate scripts
    proj_script = out_dir / "scripts" / "project_manifold.py"
    proj_script.write_text(PROJECT_MANIFOLD_SCRIPT, encoding="utf-8")
    os.chmod(proj_script, 0o755)

    gate_script = out_dir / "scripts" / "verify_dominator_gate.py"
    gate_script.write_text(DOMINATOR_GATE_SCRIPT, encoding="utf-8")
    os.chmod(gate_script, 0o755)

    landmark_by_slug = {lm["slug"]: lm for lm in (manifold_atlas.get("landmarks") or [])}
    stage_lines: list[str] = []
    oracle_scripts: list[str] = []

    for idx, m in enumerate(ordered_members, start=1):
        sid = str(m.get("id") or "")
        slug = slug_of(sid)
        rp = m.get("role_posterior") or role_posterior(m)
        top_role = max(rp.items(), key=lambda kv: kv[1])[0]
        ldir = Path(str(m.get("local_dir") or ""))
        lm_meta = landmark_by_slug.get(slug, {})
        coords_str = ", ".join(f"{c:+.2f}" for c in (lm_meta.get("chart_coordinates") or [])) or "0.00"

        body = str(m.get("github_description") or "")
        if (ldir / "SKILL.md").is_file():
            body = strip_frontmatter((ldir / "SKILL.md").read_text(encoding="utf-8", errors="replace"))

        ref_rel = f"references/members/{slug}.md"
        (out_dir / ref_rel).write_text(
            f"# Landmark Anchor on $\\mathcal{{M}}$: `{slug}`\n"
            f"- **Upstream ID**: `{sid}`\n"
            f"- **Primary Kleisli Role**: `{top_role}`\n"
            f"- **Fisher–Rao Tangent Coordinates $\\theta^{{({idx})}}$**: `[{coords_str}]`\n\n"
            f"{body}\n",
            encoding="utf-8",
        )

        member_scripts: list[str] = []
        sdir = ldir / "scripts"
        if sdir.is_dir():
            for sf in sorted(sdir.iterdir()):
                if sf.is_file() and sf.name not in {"project_manifold.py", "verify_dominator_gate.py"}:
                    dst_sf = out_dir / "scripts" / sf.name
                    shutil.copy2(sf, dst_sf)
                    os.chmod(dst_sf, 0o755)
                    oracle_scripts.append(sf.name)
                    member_scripts.append(f"`scripts/{sf.name}`")

        oracle_hint = f" *(Exogenous helper: {', '.join(member_scripts)})*" if member_scripts else ""
        stage_lines.append(
            f"{idx}. **`{top_role}` (`θ=[{coords_str}]`) — [{slug}](./{ref_rel})**: {m.get('github_description', '')}{oracle_hint}"
        )

    pb = graph.get("pullback") or {}
    chart_vars = list((manifold_atlas["logic"].get("chart_variables") or {}).keys())
    chart_summary = ", ".join(f"`{ax}`" for ax in chart_vars) if chart_vars else "*(pure conormal invariant core)*"
    skill_rel_base = f".agents/skills/{skill_name}"
    helper_block = "\n".join(
        f"   - Run `python3 {skill_rel_base}/scripts/{s} ...` on real workspace inputs/outputs."
        for s in oracle_scripts
    )
    if helper_block:
        helper_block = "\n" + helper_block

    skill_md = f"""---
name: {skill_name}
description: >-
  Lawvere-Amari generative manifold & Kleisli-composed {domain} skill ({query}) synthesized by
  /skillcompose. Maps each input x onto Fisher-Rao tangent coordinates and anti-unified logical
  fibers to synthesize global sheaf-consistent structured outputs beyond the union of member skills.
---

# `{skill_name}` — Lawvere–Amari Generative Manifold Transducer (`/skillcompose`)

This skill is **not** a prompt concatenation ($\\bigwedge_i Q_i$) nor a discrete router/union ($\\bigcup_i s_i$). It compiles {len(ordered_members)} landmark modules into a **Conditional Statistical–Logical Manifold** $\\mathfrak{{G}}_{{\\mathcal{{M}}}}$ ($x \\xrightarrow{{\\sigma^*}} \\theta^*(x) \\xrightarrow{{K_{{\\theta^*}}}} \\Gamma(\\mathcal{{U}}, \\mathcal{{F}}_{{\\theta^*(x)}})$) with anti-unified tangent axes ({chart_summary}):

{chr(10).join(stage_lines)}

Manifold atlas & chart equations: [MANIFOLD_ATLAS.md](./references/MANIFOLD_ATLAS.md) · Wiring contract: [WIRING_CONTRACT.md](./references/WIRING_CONTRACT.md).

## Mandatory Execution Protocol

1. **Stage 1 — Chart Projection & Contradiction-Free Fiber Lock ($\\sigma^* : \\mathcal{{X}} \\to \\Theta$)**:
   - Project the user's task onto the manifold before writing deliverables:
     ```bash
     python3 {skill_rel_base}/scripts/project_manifold.py \\
       --input "<task_summary_or_prompt_file>" \\
       --out "/tmp/manifold_section_{skill_name}_$$.json"
     ```
   - If `project_manifold.py` exits `2` (`ABSTAIN_OFF_MANIFOLD`), halt cleanly, do **not** generate off-domain deliverables, and report refusal.
   - Read the landmark module references in `./references/members/` needed to cover all required output facets. Whenever two landmarks specialize conflicting narrow shortcuts (which would collapse under naive conjunction $\\bigwedge_i Q_i$), resolve them via `resolved_lawvere_fiber` and the **Conormal Universal Invariants** ($\\Phi_{{\\text{{core}}}}$: exogenous verification, non-silent quarantine/rollback, causal/epistemic soundness, and sheaf global section $\\delta^0(y)=0$), locking your chosen invariants in `"/tmp/locked_contract_{skill_name}_$$.json"`.
2. **Stage 2 — Geodesic Synthesis & Global Sheaf Gluing ($\\Gamma(\\mathcal{{U}}, \\mathcal{{F}}) = \\ker \\delta^0$)**:
   - Synthesize the complete structured output bundle $y = (y_u)_{{u \\in \\mathcal{{U}}}}$ governed by `map_structured_output` (recombining capabilities across landmarks rather than dropping facets).
   - Enforce Kleisli synthesis invariants: **Idempotence ($f \\circ f = f$)** across state/schema transitions, **Zero TOCTOU & Strict Sort Separation** at validation/grammar boundaries, and **Exact Structural Envelope & Anti-Slop** (zero unrequested wrapper headings, unsupported causal claims, or contrastive-negation clichés).
   - Enforce Sheaf Restriction & Pullback Invariant (`{pb.get('key')}`): `{pb.get('invariant')}`. Coupled JSON/artifact views must satisfy exact restriction equality ($\\delta^0(y) = 0$) on all shared overlap keys.
3. **Stage 3 — Exogenous Observation & Read-Only Post-Dominator Gate ($\\mathcal{{W}}(S_{{\\text{{gate}}}}) = \\emptyset$)**:{helper_block}
   - Run deterministic tests in `/tmp/` (never citing ephemeral `/tmp/` or `.agents/` paths inside shipped reports) and certify via the read-only post-dominator & sheaf coboundary gate (passing `--glue left.json:right.json:key1,key2` for coupled JSON views):
     ```bash
     python3 {skill_rel_base}/scripts/verify_dominator_gate.py \\
       --manifold-section "/tmp/manifold_section_{skill_name}_$$.json" \\
       --contract "/tmp/locked_contract_{skill_name}_$$.json" \\
       --protect <each_deliverable_file> \\
       --glue <left_view.json>:<right_view.json>:<shared_key1>,<shared_key2> \\
       --cmd "<your_verification_test_command>"
     ```
   - **Never declare `DONE` until `verify_dominator_gate.py` prints `"decision": "PASS"` (exit `0`).**
"""
    (out_dir / "SKILL.md").write_text(skill_md, encoding="utf-8")

    # Write references metadata AFTER SKILL.md so verify_graph measures exact Parnas encapsulation ratio!
    (out_dir / "references" / "MANIFOLD_ATLAS.md").write_text(render_manifold_md(manifold_atlas), encoding="utf-8")
    (out_dir / "references" / "manifold_atlas.json").write_text(
        json.dumps(manifold_atlas, indent=2) + "\n", encoding="utf-8"
    )
    (out_dir / "references" / "WIRING_CONTRACT.md").write_text(render_wiring_md(graph), encoding="utf-8")
    (out_dir / "references" / "selection_certificate.json").write_text(
        json.dumps(sel_report, indent=2) + "\n", encoding="utf-8"
    )
    graph["verification"] = verify_graph(graph, out_dir)
    (out_dir / "references" / "wiring_graph.json").write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")

    from export_platform_targets import stamp_in_place

    stamp_in_place(out_dir, skill_name)

    return {
        "ok": graph["verification"]["decision"] == "PASS",
        "skill_dir": str(out_dir),
        "skill_md_bytes": (out_dir / "SKILL.md").stat().st_size,
        "chosen_ids": [m.get("id") for m in ordered_members],
        "oracle_scripts": oracle_scripts + ["project_manifold.py", "verify_dominator_gate.py"],
        "nemhauser_wolsey_certificate": sel_report["nemhauser_wolsey_certificate"],
        "lift_over_popularity_top_n": sel_report["lift_over_popularity_top_n"],
        "counterfactual_popularity_top_n": sel_report["counterfactual_popularity_top_n"],
        "manifold_telemetry": {
            "tangent_rank": manifold_atlas["geometry"]["tangent_rank"],
            "intrinsic_dimension": manifold_atlas["geometry"]["intrinsic_dimension_participation_ratio"],
            "fisher_logdet_volume": manifold_atlas["geometry"]["fisher_logdet_volume"],
            "amari_e_vs_m_bregman_gap_bits": manifold_atlas["geometry"]["amari_e_vs_m_bregman_gap_bits"],
            "union_fiber_size": manifold_atlas["logic"]["union_fiber_size"],
            "manifold_total_fiber_size": manifold_atlas["logic"]["manifold_total_fiber_size"],
            "recombinant_novel_states": manifold_atlas["logic"]["recombinant_novel_states"],
            "specialization_exact": manifold_atlas["logic"]["specialization_exact"],
        },
        "generalization_over_union": gen_proof,
        "verification": graph["verification"],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--candidates", type=Path, required=True)
    ap.add_argument("--n", type=int, default=4)
    ap.add_argument("--domain", default="general")
    ap.add_argument("--query", default="")
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--skill-name", default="domain-pack")
    ap.add_argument("--upstreams-root", type=Path, default=None)
    ap.add_argument("--seed", default="skillcompose")
    args = ap.parse_args()

    res = compose_package(
        args.candidates,
        n=args.n,
        domain=args.domain,
        query=args.query,
        out_dir=args.out_dir,
        skill_name=args.skill_name,
        upstreams_root=args.upstreams_root,
        seed=args.seed,
    )
    print(json.dumps(res, indent=2))
    return 0 if res["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
