#!/usr/bin/env python3
"""Measure adversarial CLI / empty-WIP refusal rate for skillremix.

Runs fixture cases against parse_args.py + resume_forge.py and records
pass_rate (fraction that correctly refuse or accept).
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SKILL_ROOT = ROOT.parent.parent
SCRIPTS = SKILL_ROOT / "scripts"

# Prefer a known good WIP if present; else skip the accept case.
GOOD_WIPS = [
    Path("/Users/halley/linkedin/skillremix-wip-20260721T000558Z"),
    Path("/Users/halley/linkedin/skillremix-wip-20260721T000113Z"),
    Path("/Users/halley/Documents/linkedin-1/skillremix-wip-20260720T232557Z"),
    Path("/Users/halley/Documents/linkedin-1/skillremix-wip-20260721T000933Z"),
]


def run(cmd: list[str]) -> tuple[int, str]:
    p = subprocess.run(cmd, capture_output=True, text=True)
    out = (p.stdout or "") + (p.stderr or "")
    return p.returncode, out


def score() -> dict:
    cases: list[dict] = []

    def expect_fail(name: str, cmd: list[str], error_substr: str | None = None) -> None:
        code, out = run(cmd)
        ok = code != 0
        if error_substr and error_substr not in out:
            ok = False
        # Must not invent fork_dir from cwd
        if '"fork_dir": "mm-claim-audit"' in out or '"fork_dir":"mm-claim-audit"' in out:
            ok = False
        cases.append({"name": name, "ok": ok, "exit": code})

    def expect_ok(name: str, cmd: list[str], require_keys: list[str] | None = None) -> None:
        code, out = run(cmd)
        ok = code == 0
        if require_keys:
            try:
                data = json.loads(out)
            except json.JSONDecodeError:
                data = {}
                ok = False
            for k in require_keys:
                if k not in data or data[k] in (None, ""):
                    ok = False
        cases.append({"name": name, "ok": ok, "exit": code})

    py = sys.executable
    parse = py, str(SCRIPTS / "parse_args.py")
    status = py, str(SCRIPTS / "resume_forge.py"), "status"

    expect_fail("parse_status_no_wip", [*parse, "--status"], "wip_required")
    expect_fail("parse_resume_no_wip", [*parse, "--resume"], "wip_required")
    expect_fail("status_empty_wip", [*status, "--wip", "", "--json"], "wip_invalid")
    expect_fail("status_cwd_wip", [*status, "--wip", ".", "--json"], "wip_invalid")
    expect_fail(
        "status_non_wip_name",
        [*status, "--wip", str(SKILL_ROOT), "--json"],
        "wip_name",
    )

    pin = py, str(SCRIPTS / "pin_fastpath.py")
    expect_fail(
        "pin_below_floor",
        [
            *pin,
            "--pin",
            "vercel-labs/agent-skills@web-design-guidelines",
            "--min-installs",
            "999999999",
            "--min-stars",
            "999999999",
            "--json",
        ],
        "below_adoption_floor",
    )
    expect_ok(
        "pin_below_floor_allow",
        [
            *pin,
            "--pin",
            "vercel-labs/agent-skills@web-design-guidelines",
            "--min-installs",
            "999999999",
            "--min-stars",
            "999999999",
            "--allow-below-floor",
            "--json",
        ],
        require_keys=["ok", "chosen"],
    )

    lic = py, str(SCRIPTS / "license_gate.py")
    expect_fail("license_gpl_fail", [*lic, "--license", "gpl-3.0", "--json"], "gpl")
    expect_ok(
        "license_mit_pass",
        [*lic, "--license", "mit", "--json"],
        require_keys=["decision"],
    )

    good = next((p for p in GOOD_WIPS if p.is_dir()), None)
    if good:
        expect_ok(
            "status_valid_wip",
            [*status, "--wip", str(good), "--json"],
            require_keys=["mode", "resume_hint", "wip"],
        )
        expect_fail(
            "contradictory_status_resume",
            [*parse, "--status", "--resume", "--wip", str(good)],
            "contradictory_flags",
        )
        expect_fail(
            "contradictory_discover_resume",
            [*parse, "--discover-only", "--resume", "--wip", str(good)],
            "contradictory_flags",
        )
    else:
        cases.append({"name": "status_valid_wip", "ok": False, "exit": -1, "skip_reason": "no fixture WIP"})
        cases.append({"name": "contradictory_status_resume", "ok": False, "exit": -1, "skip_reason": "no fixture WIP"})
        cases.append({"name": "contradictory_discover_resume", "ok": False, "exit": -1, "skip_reason": "no fixture WIP"})

    passed = sum(1 for c in cases if c["ok"])
    total = len(cases)
    refusal_names = {
        "parse_status_no_wip",
        "parse_resume_no_wip",
        "status_empty_wip",
        "status_cwd_wip",
        "status_non_wip_name",
        "contradictory_status_resume",
        "contradictory_discover_resume",
        "pin_below_floor",
        "license_gpl_fail",
    }
    return {
        "skill_root": str(SKILL_ROOT),
        "cases": cases,
        "passed": passed,
        "total": total,
        "pass_rate": round(passed / total, 4) if total else 0.0,
        "refusal_cases_ok": all(c["ok"] for c in cases if c["name"] in refusal_names),
    }


def main() -> None:
    values = score()
    sample = {
        "metric_id": "adversarial-args",
        "title": "Adversarial args / empty-WIP refusal rate",
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
