#!/usr/bin/env python3
"""Busy-lock for skillremix forge so 90s wakes skip while the agent is mid-round.

Lock path: $WIP_DIR/forge/agent_busy.lock

  acquire  — call at the START of a forge round (agent still working)
  release  — call after forge_round.sh logs (or on abort)
  check    — exit 0 if busy (fresh), 1 if free/stale; JSON on stdout with --json
"""
from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

# Stale after this many seconds → treat as free (crashed agent)
DEFAULT_MAX_AGE_SEC = 45 * 60


def lock_path(wip: Path) -> Path:
    return wip / "forge" / "agent_busy.lock"


def read_lock(path: Path) -> dict | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"raw": True, "started_at": path.stat().st_mtime}


def is_busy(wip: Path, max_age_sec: float) -> tuple[bool, dict]:
    path = lock_path(wip)
    data = read_lock(path)
    if not data:
        return False, {"busy": False, "path": str(path)}
    started = float(data.get("started_at") or 0)
    age = time.time() - started if started else 0.0
    if age > max_age_sec:
        return False, {
            "busy": False,
            "stale": True,
            "age_sec": round(age, 1),
            "max_age_sec": max_age_sec,
            "path": str(path),
            "lock": data,
        }
    return True, {
        "busy": True,
        "age_sec": round(age, 1),
        "path": str(path),
        "lock": data,
    }


def acquire(wip: Path, round_n: int | None, note: str) -> dict:
    path = lock_path(wip)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "started_at": time.time(),
        "pid": os.getpid(),
        "round": round_n,
        "note": note or "forge-round-in-progress",
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return {"ok": True, "acquired": True, "path": str(path), "lock": payload}


def release(wip: Path) -> dict:
    path = lock_path(wip)
    existed = path.is_file()
    if existed:
        path.unlink()
    return {"ok": True, "released": existed, "path": str(path)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("action", choices=("acquire", "release", "check"))
    ap.add_argument("--wip", type=Path, required=True)
    ap.add_argument("--round", type=int, default=None)
    ap.add_argument("--note", default="")
    ap.add_argument("--max-age-sec", type=float, default=DEFAULT_MAX_AGE_SEC)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if args.action == "acquire":
        out = acquire(args.wip, args.round, args.note)
        rc = 0
    elif args.action == "release":
        out = release(args.wip)
        rc = 0
    else:
        busy, out = is_busy(args.wip, args.max_age_sec)
        rc = 0 if busy else 1

    print(json.dumps(out, indent=2) if args.json else json.dumps(out))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
