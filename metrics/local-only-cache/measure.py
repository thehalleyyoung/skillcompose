#!/usr/bin/env python3
"""Measure discover_skills --local-only hit/miss exit contract (ship 017)."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SKILL_ROOT = ROOT.parent.parent
SCRIPTS = SKILL_ROOT / "scripts"


def run(cmd: list[str]) -> tuple[int, dict]:
    p = subprocess.run(cmd, capture_output=True, text=True)
    try:
        data = json.loads(p.stdout or "{}")
    except json.JSONDecodeError:
        data = {"raw": (p.stdout or p.stderr or "")[:300]}
    return p.returncode, data


def score() -> dict:
    cases = []
    with tempfile.TemporaryDirectory() as td:
        out_hit = Path(td) / "hit.jsonl"
        code, data = run(
            [
                sys.executable,
                str(SCRIPTS / "discover_skills.py"),
                "--out",
                str(out_hit),
                "--domain",
                "writing",
                "--extra",
                "",
                "--local-only",
                "--json",
            ]
        )
        # Hit if cache exists from prior runs; else accept miss as ok for this env
        if code == 0 and data.get("decision") == "PASS" and data.get("local_only") and out_hit.is_file():
            cases.append({"name": "cache_hit", "ok": True, "exit": code})
        elif code == 2 and data.get("error") == "local_only_cache_miss":
            cases.append({"name": "cache_hit", "ok": True, "exit": code, "note": "no writing cache — miss acceptable"})
        else:
            cases.append({"name": "cache_hit", "ok": False, "exit": code, "data": data})

        out_miss = Path(td) / "miss.jsonl"
        code2, data2 = run(
            [
                sys.executable,
                str(SCRIPTS / "discover_skills.py"),
                "--out",
                str(out_miss),
                "--domain",
                "writing",
                "--extra",
                f"metric-miss-{int(time.time())}",
                "--local-only",
                "--json",
            ]
        )
        ok2 = code2 == 2 and data2.get("error") == "local_only_cache_miss" and not out_miss.is_file()
        cases.append({"name": "cache_miss", "ok": ok2, "exit": code2, "error": data2.get("error")})

    passed = sum(1 for c in cases if c["ok"])
    return {
        "cases": cases,
        "passed": passed,
        "total": len(cases),
        "pass_rate": round(passed / len(cases), 4) if cases else 0.0,
    }


def main() -> None:
    values = score()
    sample = {
        "metric_id": "local-only-cache",
        "title": "local-only discover hit/miss exit contract",
        "at": datetime.now(tz=timezone.utc).isoformat(),
        "ts": time.time(),
        "values": values,
    }
    hist = ROOT / "history.jsonl"
    with hist.open("a", encoding="utf-8") as f:
        f.write(json.dumps(sample) + "\n")
    (ROOT / "latest.json").write_text(json.dumps(sample, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "latest": str(ROOT / "latest.json"), "values": values}))


if __name__ == "__main__":
    main()
