#!/usr/bin/env python3
"""Exit 0 if review/last_dry_run.json mode=full; else exit 2."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    stamp = args.root / "review" / "last_dry_run.json"
    if not stamp.is_file():
        out = {"ok": False, "error": "stamp_missing", "path": str(stamp),
               "hint": "bash scripts/dry_run_gates.sh  # full, no --fast"}
        print(json.dumps(out, indent=2))
        return 2
    st = json.loads(stamp.read_text(encoding="utf-8"))
    ok = st.get("mode") == "full" and st.get("pass") is True
    out = {"ok": ok, "stamp": st, "path": str(stamp)}
    if not ok:
        out["error"] = "mode_not_full"
        out["hint"] = "bash scripts/dry_run_gates.sh  # without --fast"
    print(json.dumps(out, indent=2))
    return 0 if ok else 2

if __name__ == "__main__":
    raise SystemExit(main())
