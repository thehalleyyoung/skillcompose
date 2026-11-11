#!/usr/bin/env python3
"""Mechanical Kleisli Skill Composer for /skillcompose.

Takes a candidate pool (JSONL/JSON with materialized `local_dir` or `--upstreams-root`), runs:
  1. Submodular JSD + Kolmogorov/NCD selection with Nemhauser-Wolsey optimality certificate
  2. Static capability/script auditing (`audit_incumbent.py`)
  3. Algebraic Kleisli wiring compilation (`wiring_compiler.py`)
  4. Parnas-encapsulated composite package synthesis (`SKILL.md`, `references/members/*.md`,
     `scripts/*`, and auto-generated `scripts/verify_dominator_gate.py` enforcing W(gate) == empty)
  5. Post-materialization static theorem verification (all 5 algebraic laws including Parnas ratio).
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
from submodular_select import build_selection_report, role_posterior  # noqa: E402
from wiring_compiler import compile_wiring, render_wiring_md, slug_of, verify_graph  # noqa: E402

DOMINATOR_GATE_SCRIPT = """#!/usr/bin/env python3
\"\"\"Auto-generated Read-Only Post-Dominator Gate & Separation-Logic Frame Checker (/skillcompose).

Mechanically enforces:
  1. Exogenous Grounding (DPI escape): executes deterministic verification commands and checks exit == 0.
  2. Orthogonal Critic Non-Interference (W(gate) == empty): snapshots SHA-256 digests of protected
     deliverables BEFORE running checks and fails (exit 2) if any check mutates a deliverable.
  3. Sufficient-Statistic Contract Check: validates optional JSON contract file if supplied.
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


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--protect", action="append", default=[], help="Deliverable path that must exist and remain unmutated")
    ap.add_argument("--contract", type=Path, default=None, help="Optional JSON sufficient-statistic contract to validate")
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
        "exogenous_commands_run": len(cmd_traces),
        "separation_logic_clean": len(mutated) == 0,
        "reasons": reasons,
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

    graph = compile_wiring(chosen, audits, domain=domain, package_name=skill_name)

    if out_dir.exists():
        shutil.rmtree(out_dir)
    (out_dir / "references" / "members").mkdir(parents=True, exist_ok=True)
    (out_dir / "scripts").mkdir(parents=True, exist_ok=True)

    # Write auto-generated Post-Dominator Gate script
    gate_script = out_dir / "scripts" / "verify_dominator_gate.py"
    gate_script.write_text(DOMINATOR_GATE_SCRIPT, encoding="utf-8")
    os.chmod(gate_script, 0o755)

    # Order members along Kleisli causal flow
    def member_sort_key(m: dict[str, Any]) -> tuple[int, str]:
        rp = m.get("role_posterior") or role_posterior(m)
        top_role = max(rp.items(), key=lambda kv: kv[1])[0]
        return (STAGE_PRIORITY.get(top_role, 3), str(m.get("id") or ""))

    ordered_members = sorted(chosen, key=member_sort_key)
    stage_lines: list[str] = []
    oracle_scripts: list[str] = []

    for idx, m in enumerate(ordered_members, start=1):
        sid = str(m.get("id") or "")
        slug = slug_of(sid)
        rp = m.get("role_posterior") or role_posterior(m)
        top_role = max(rp.items(), key=lambda kv: kv[1])[0]
        ldir = Path(str(m.get("local_dir") or ""))

        body = str(m.get("github_description") or "")
        if (ldir / "SKILL.md").is_file():
            body = strip_frontmatter((ldir / "SKILL.md").read_text(encoding="utf-8", errors="replace"))

        ref_rel = f"references/members/{slug}.md"
        (out_dir / ref_rel).write_text(
            f"# Encapsulated Module: `{slug}`\n"
            f"- **Upstream ID**: `{sid}`\n"
            f"- **Primary Kleisli Role**: `{top_role}`\n\n"
            f"{body}\n",
            encoding="utf-8",
        )

        member_scripts: list[str] = []
        sdir = ldir / "scripts"
        if sdir.is_dir():
            for sf in sorted(sdir.iterdir()):
                if sf.is_file():
                    dst_sf = out_dir / "scripts" / sf.name
                    shutil.copy2(sf, dst_sf)
                    os.chmod(dst_sf, 0o755)
                    oracle_scripts.append(sf.name)
                    member_scripts.append(f"`scripts/{sf.name}`")

        oracle_hint = f" *(Exogenous helper: {', '.join(member_scripts)})*" if member_scripts else ""
        stage_lines.append(
            f"{idx}. **`{top_role}` — [{slug}](./{ref_rel})**: {m.get('github_description', '')}{oracle_hint}"
        )

    pb = graph.get("pullback") or {}
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
  Principled Kleisli-composed {domain} skill ({query}) synthesized by /skillcompose with Parnas progressive disclosure, pullback consistency, and an orthogonal read-only post-dominator gate.
---

# `{skill_name}` — Kleisli Transducer Pipeline (`/skillcompose`)

This skill composes {len(ordered_members)} complementary modules as a **typed Kleisli pipeline** ($S_{{\\text{{gate}}}} \\circ S_{{\\text{{exec}}}} \\circ (S_1 \\times_K S_2) \\circ_\\alpha S_{{\\text{{spec}}}}$) rather than a flat prompt dump. Read each module's encapsulated spec in `./references/members/` right before executing its stage (preserving Attention Channel SNR):

{chr(10).join(stage_lines)}

Full formal wiring contract: [WIRING_CONTRACT.md](./references/WIRING_CONTRACT.md).

## Mandatory Execution Protocol

1. **Stage 1 — Sufficient-Statistic Contract Lock ($Q_{{\\text{{spec}}}} \\implies P_{{\\text{{synth}}}}$)**:
   - Inspect all workspace files, schemas, data tables, or specifications completely first.
   - Read the `spec_grounding` / `static_contract` module reference(s) above and write a minimal sufficient-statistic contract `/tmp/locked_contract.json` enumerating every edge case, boundary condition, denominator/schema invariant, and required output artifact (plus any contract file explicitly requested by the task).
2. **Stage 2 — Contract-Bound Synthesis & Pullback Reconciliation ($\\pi_K(O_1) = \\pi_K(O_2)$)**:
   - Read the `synthesis` / `state_recovery` module reference(s) above and build all requested deliverables.
   - Enforce Pullback Invariant (`{pb.get('key')}`): `{pb.get('invariant')}`. Whenever two deliverables share schemas, numbers, function signatures, or state facts, verify exact equality programmatically via Python rather than by eye.
3. **Stage 3 — Exogenous Observation & Read-Only Post-Dominator Gate ($\\mathcal{{W}}(S_{{\\text{{gate}}}}) = \\emptyset$)**:
   - Read the `exec_observation` / `adversarial_verify` module reference(s) above.{helper_block}
   - Execute standalone tests (using `/tmp/` for any temporary copies or scratch harnesses so the workspace stays clean of unrequested files).
   - Certify completion through the read-only post-dominator gate:
     ```bash
     python3 {skill_rel_base}/scripts/verify_dominator_gate.py \\
       --contract /tmp/locked_contract.json \\
       --protect <each_deliverable_file> \\
       --cmd "<your_verification_test_command>"
     ```
   - **Never declare `DONE` until `verify_dominator_gate.py` prints `"decision": "PASS"` (exit `0`).**
"""
    (out_dir / "SKILL.md").write_text(skill_md, encoding="utf-8")

    # Write references metadata AFTER SKILL.md so verify_graph measures exact Parnas encapsulation ratio!
    (out_dir / "references" / "WIRING_CONTRACT.md").write_text(render_wiring_md(graph), encoding="utf-8")
    (out_dir / "references" / "selection_certificate.json").write_text(
        json.dumps(sel_report, indent=2) + "\n", encoding="utf-8"
    )
    graph["verification"] = verify_graph(graph, out_dir)
    (out_dir / "references" / "wiring_graph.json").write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")

    return {
        "ok": graph["verification"]["decision"] == "PASS",
        "skill_dir": str(out_dir),
        "skill_md_bytes": (out_dir / "SKILL.md").stat().st_size,
        "chosen_ids": [m.get("id") for m in ordered_members],
        "oracle_scripts": oracle_scripts + ["verify_dominator_gate.py"],
        "nemhauser_wolsey_certificate": sel_report["nemhauser_wolsey_certificate"],
        "lift_over_popularity_top_n": sel_report["lift_over_popularity_top_n"],
        "counterfactual_popularity_top_n": sel_report["counterfactual_popularity_top_n"],
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
