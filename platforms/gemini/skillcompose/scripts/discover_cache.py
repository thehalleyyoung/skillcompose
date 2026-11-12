#!/usr/bin/env python3
"""Cache discover_skills outputs by domain+query hash to cut repeat latency.

Usage:
  python3 discover_cache.py --domain devops --extra "ci" --lookup
    → prints cache path if fresh hit (exit 0) else miss (exit 1)
  python3 discover_cache.py --domain devops --extra "ci" --store PATH.jsonl
  python3 discover_cache.py --domain devops --extra "ci" --path
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import time
from pathlib import Path

DEFAULT_TTL = 3600  # 1h
CACHE_ROOT = Path.home() / ".cache" / "skillremix" / "discover"


def key(domain: str, extra: str) -> str:
    raw = f"{domain or 'general'}::{extra or ''}".encode()
    return hashlib.sha256(raw).hexdigest()[:24]


def cache_paths(domain: str, extra: str) -> tuple[Path, Path]:
    k = key(domain, extra)
    d = CACHE_ROOT / k
    return d / "candidates.jsonl", d / "meta.json"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--domain", default="general")
    ap.add_argument("--extra", default="")
    ap.add_argument("--ttl", type=int, default=DEFAULT_TTL)
    ap.add_argument("--lookup", action="store_true")
    ap.add_argument("--store", type=Path, default=None)
    ap.add_argument("--path", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    cand, meta = cache_paths(args.domain, args.extra)
    if args.path:
        print(json.dumps({"candidates": str(cand), "meta": str(meta)}))
        return 0

    if args.store:
        cand.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(args.store, cand)
        meta.write_text(
            json.dumps(
                {
                    "domain": args.domain,
                    "extra": args.extra,
                    "stored_at": time.time(),
                    "src": str(args.store),
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        print(json.dumps({"ok": True, "stored": str(cand)}))
        return 0

    if args.lookup:
        if not cand.is_file() or not meta.is_file():
            print(json.dumps({"ok": False, "error": "miss"}))
            return 1
        m = json.loads(meta.read_text(encoding="utf-8"))
        age = time.time() - float(m.get("stored_at") or 0)
        if age > args.ttl:
            print(json.dumps({"ok": False, "error": "stale", "age_sec": age}))
            return 1
        print(json.dumps({"ok": True, "candidates": str(cand), "age_sec": age, "meta": m}))
        return 0

    ap.error("pass --lookup, --store, or --path")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
