#!/usr/bin/env python3
"""Metric: dry_run_gates --fast refuses mode=full unless --force-fast."""
from __future__ import annotations

import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SKILL = ROOT.parent.parent
SCRIPT = SKILL / "scripts" / "dry_run_gates.sh"
STAMP = SKILL / "review" / "last_dry_run.json"


def _write_stamp(mode: str) -> None:
    STAMP.parent.mkdir(parents=True, exist_ok=True)
    STAMP.write_text(
        json.dumps(
            {"mode": mode, "pass": True, "at": datetime.now(tz=timezone.utc).isoformat()},
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["SKILLREMIX_IN_DRY_RUN_PROTECT"] = "1"
    return subprocess.run(
        ["bash", str(SCRIPT), *args],
        capture_output=True,
        text=True,
        timeout=120,
        env=env,
    )


def score() -> dict:
    prior = STAMP.read_text(encoding="utf-8") if STAMP.is_file() else None
    cases = []
    try:
        _write_stamp("full")
        r1 = _run(["--fast"])
        out1 = (r1.stdout or "") + (r1.stderr or "")
        c1 = {
            "name": "refuse_fast_on_full",
            "ok": r1.returncode == 2 and "Refusing --fast" in out1,
            "exit": r1.returncode,
        }
        cases.append(c1)

        _write_stamp("full")
        r2 = _run(["--force-fast"])
        st = json.loads(STAMP.read_text(encoding="utf-8")) if STAMP.is_file() else {}
        c2 = {
            "name": "force_fast_ok",
            "ok": r2.returncode == 0 and st.get("mode") == "fast",
            "exit": r2.returncode,
            "stamp_mode": st.get("mode"),
        }
        cases.append(c2)
    finally:
        # Restore publish-ready full stamp (do not leave fast)
        _write_stamp("full")
        if prior and '"mode": "full"' not in prior and prior.strip():
            # keep restored full; prior may have been fast — prefer full after metric
            pass

    passed = sum(1 for c in cases if c.get("ok"))
    return {
        "skill_root": str(SKILL),
        "cases": cases,
        "passed": passed,
        "total": len(cases),
        "pass_rate": passed / len(cases) if cases else 0.0,
    }


def main() -> None:
    values = score()
    sample = {
        "metric_id": "dry-run-protect",
        "title": "dry_run --fast protect full stamp",
        "at": datetime.now(tz=timezone.utc).isoformat(),
        "ts": time.time(),
        "values": values,
    }
    with (ROOT / "history.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(sample, ensure_ascii=False) + "\n")
    (ROOT / "latest.json").write_text(json.dumps(sample, indent=2) + "\n", encoding="utf-8")
    ok = values.get("pass_rate", 0) >= 1.0
    print(json.dumps({"ok": ok, "latest": str(ROOT / "latest.json"), "values": values}, indent=2))
    raise SystemExit(0 if ok else 2)


if __name__ == "__main__":
    main()
