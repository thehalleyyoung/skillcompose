#!/usr/bin/env python3
"""Refuse Phase 2+ forge actions when early-stop modes are set (false-done guard).

Transfer from rtl-closure / verify-before-done lessons: do not let agents
"helpfully" continue into clone/forge after --discover-only / --audit-only /
--remix-plan-only.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


STOP_FLAGS = ("discover_only", "audit_only", "remix_plan_only", "status")
# Read-only / parse actions stay allowed under early-stop (UC04)
ALLOW_ACTIONS = frozenset({"status", "parse", "plan", "coherence", "pick", "discover"})


def check(args: dict, *, action: str) -> dict:
    act = (action or "").strip().lower()
    if act in ALLOW_ACTIONS:
        return {"ok": True, "action": action, "allowed": True}
    hit = [k for k in STOP_FLAGS if args.get(k)]
    if hit:
        return {
            "ok": False,
            "error": "mode_guard",
            "message": f"refusing action {action!r} while stop flags set: {hit}",
            "flags": hit,
            "hint": "early-stop mode — print results and exit; do not clone/forge",
        }
    return {"ok": True, "action": action}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--args-json", type=Path, help="parse_args JSON file")
    ap.add_argument("--action", default="forge", help="action label being attempted")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    if args.args_json:
        data = json.loads(args.args_json.read_text(encoding="utf-8"))
    else:
        data = json.loads(sys.stdin.read() or "{}")
    out = check(data, action=args.action)
    print(json.dumps(out, indent=2) if args.json else json.dumps(out))
    return 0 if out.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
