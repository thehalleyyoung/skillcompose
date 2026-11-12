#!/usr/bin/env python3
"""Auto-generated Read-Only Post-Dominator, Sheaf Gluing & Separation-Logic Gate (/skillcompose).

Mechanically enforces:
  1. Exogenous Grounding (DPI escape): executes deterministic verification commands and checks exit == 0.
  2. Orthogonal Critic Non-Interference (W(gate) == empty): snapshots SHA-256 digests of protected
     deliverables BEFORE running checks and fails (exit 2) if any check mutates a deliverable.
  3. Sufficient-Statistic & Manifold Section Check: validates JSON contract and optional projected
     manifold section (`SYNTHESIZE_ON_MANIFOLD`, non-empty admissible fiber).
  4. Cech Sheaf 0-Coboundary Check (`--glue left.json:right.json:key1,key2`): deterministically verifies
     exact restriction agreement rho_u(y_u) == rho_v(y_v) across overlapping structured outputs.
"""
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
