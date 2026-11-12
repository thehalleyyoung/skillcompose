#!/usr/bin/env python3
"""Ensure forge log covers all 4 phases with correct kinds (replaces check_themes T1–T5)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from forge_phases import FORGE_ROUNDS, validate_log_phases  # noqa: E402


def load_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--phases", type=Path, help="forge_phases.json (optional; ranges are fixed)")
    ap.add_argument("--themes", type=Path, help="Legacy alias for --phases")
    ap.add_argument("--log", type=Path, required=True)
    ap.add_argument("--rounds", type=int, default=FORGE_ROUNDS)
    ap.add_argument("--json", action="store_true")
    # Accept legacy flag without failing
    ap.add_argument("--min-rounds-per-theme", type=int, default=None, help=argparse.SUPPRESS)
    args = ap.parse_args()

    rows = load_jsonl(args.log)
    out = validate_log_phases(rows, args.rounds)
    # Also require every phase id present in optional phases file
    phases_path = args.phases or args.themes
    if phases_path and phases_path.is_file():
        doc = json.loads(phases_path.read_text(encoding="utf-8"))
        expected = doc.get("phases") or doc.get("themes") or []
        if expected and len(expected) not in (0, 4):
            out["reasons"] = list(out.get("reasons") or []) + [
                f"expected 4 phases in plan file, got {len(expected)} (T1–T5 ladder is retired)"
            ]
            out["decision"] = "FAIL"
    print(json.dumps(out, indent=2) if args.json else out)
    return 0 if out["decision"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
