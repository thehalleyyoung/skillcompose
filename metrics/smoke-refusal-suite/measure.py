#!/usr/bin/env python3
"""Measure offline smoke_test.sh (incl. refusal suite). Append history + latest.json."""

from __future__ import annotations

import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SKILL_ROOT = ROOT.parent.parent
SMOKE = SKILL_ROOT / "scripts" / "smoke_test.sh"


def score() -> dict:
    t0 = time.time()
    if not SMOKE.is_file():
        return {
            "skill_root": str(SKILL_ROOT),
            "smoke_ok": False,
            "error": "missing_smoke_test",
            "elapsed_ms": 0,
        }
    proc = subprocess.run(
        ["bash", str(SMOKE)],
        capture_output=True,
        text=True,
        timeout=180,
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    elapsed_ms = int((time.time() - t0) * 1000)
    return {
        "skill_root": str(SKILL_ROOT),
        "exit_code": proc.returncode,
        "smoke_ok": proc.returncode == 0 and "SMOKE_OK" in out,
        "has_refusal_suite": "Refusal suite" in SMOKE.read_text(encoding="utf-8"),
        "elapsed_ms": elapsed_ms,
        "tail": "\n".join(out.strip().splitlines()[-5:]),
    }


def main() -> None:
    values = score()
    sample = {
        "metric_id": "smoke-refusal-suite",
        "title": "Smoke refusal suite green",
        "at": datetime.now(tz=timezone.utc).isoformat(),
        "ts": time.time(),
        "values": values,
    }
    hist = ROOT / "history.jsonl"
    with hist.open("a", encoding="utf-8") as f:
        f.write(json.dumps(sample, ensure_ascii=False) + "\n")
    (ROOT / "latest.json").write_text(json.dumps(sample, indent=2) + "\n", encoding="utf-8")
    ok = bool(values.get("smoke_ok"))
    print(json.dumps({"ok": ok, "latest": str(ROOT / "latest.json"), "values": values}, indent=2))
    raise SystemExit(0 if ok else 2)


if __name__ == "__main__":
    main()
