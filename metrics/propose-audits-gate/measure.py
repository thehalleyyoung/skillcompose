#!/usr/bin/env python3
"""Measure propose_remix fails closed when audits are missing (ship 008)."""

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
FIX = ROOT / "fixtures"


def run(cmd: list[str]) -> tuple[int, dict]:
    p = subprocess.run(cmd, capture_output=True, text=True)
    try:
        data = json.loads(p.stdout or "{}")
    except json.JSONDecodeError:
        data = {"raw": (p.stdout or p.stderr or "")[:300]}
    return p.returncode, data


def score() -> dict:
    FIX.mkdir(parents=True, exist_ok=True)
    chosen = {
        "chosen": [
            {
                "id": "example/a@alpha",
                "installs": 100,
                "discovery_role": "domain_core",
            },
            {
                "id": "example/b@beta",
                "installs": 100,
                "discovery_role": "domain_core",
            },
        ],
        "ids": ["example/a@alpha", "example/b@beta"],
    }
    chosen_path = FIX / "chosen_n_no_audits.json"
    chosen_path.write_text(json.dumps(chosen, indent=2), encoding="utf-8")

    cases = []
    with tempfile.TemporaryDirectory() as td:
        audits = Path(td) / "audits"
        audits.mkdir()
        out = Path(td) / "plan.json"
        code, data = run(
            [
                sys.executable,
                str(SCRIPTS / "propose_remix.py"),
                "--chosen-n",
                str(chosen_path),
                "--audits",
                str(audits),
                "--out",
                str(out),
                "--domain",
                "writing",
                "--json",
            ]
        )
        ok = (
            code == 2
            and data.get("decision") == "FAIL"
            and data.get("error") == "audits_incomplete"
            and not out.exists()
        )
        cases.append({"name": "empty_audits_fail", "ok": ok, "exit": code, "decision": data.get("decision")})

        out2 = Path(td) / "plan_allow.json"
        code2, data2 = run(
            [
                sys.executable,
                str(SCRIPTS / "propose_remix.py"),
                "--chosen-n",
                str(chosen_path),
                "--audits",
                str(audits),
                "--out",
                str(out2),
                "--domain",
                "writing",
                "--allow-missing-audits",
                "--json",
            ]
        )
        ok2 = (
            code2 == 0
            and data2.get("decision") == "PASS_WITH_WARNINGS"
            and out2.exists()
            and data2.get("audits_complete") is False
        )
        cases.append(
            {
                "name": "allow_missing_warn",
                "ok": ok2,
                "exit": code2,
                "decision": data2.get("decision"),
            }
        )

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
        "metric_id": "propose-audits-gate",
        "title": "propose_remix empty-audits must FAIL exit 2",
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
