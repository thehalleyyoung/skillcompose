#!/usr/bin/env python3
"""Measure compact vs --full status JSON byte budget (UC01 / ship 003)."""

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

GOOD_WIPS = [
    Path("/Users/halley/linkedin/skillremix-wip-20260721T000558Z"),
    Path("/Users/halley/linkedin/skillremix-wip-20260721T000113Z"),
]

# Compact should be < this fraction of full on large remix WIPs
MAX_RATIO = 0.25
# Absolute ceiling for default compact status on large n
MAX_COMPACT_BYTES = 12000


def _make_fixture_wip(base: Path) -> Path:
    wip = base / "skillremix-wip-20260721T000000Z"
    (wip / "discovery").mkdir(parents=True, exist_ok=True)
    (wip / "forge").mkdir(parents=True, exist_ok=True)
    chosen = []
    ids = []
    for i in range(1, 9):
        cid = f"org-{i}/skill-pack-{i}@member-skill-{i}"
        ids.append(cid)
        chosen.append(
            {
                "id": cid,
                "installs": 1200 * i,
                "stars": 150 * i,
                "license": "mit",
                "url": f"https://github.com/org-{i}/skill-pack-{i}",
                "skills_sh_url": f"https://skills.sh/org-{i}/skill-pack-{i}/member-skill-{i}",
                "discovery_role": "domain_core" if i <= 4 else "practice_support",
                "query": f"domain query {i}",
                "github_description": (
                    f"Comprehensive marketplace member skill #{i} with detailed metadata, "
                    f"audit notes, repository stats, and enrichment payload for status byte budget testing. "
                    * 4
                ),
                "pushed_at": "2026-07-20T00:00:00Z",
                "why_eligible": "meets installs and stars floor with permissive license",
            }
        )
    (wip / "discovery" / "chosen_n.json").write_text(
        json.dumps({"n": 8, "decision": "PASS", "ids": ids, "chosen": chosen}, indent=2) + "\n",
        encoding="utf-8",
    )
    return wip


def run_status(wip: Path, *extra: str) -> tuple[int, dict]:
    cmd = [
        sys.executable,
        str(SCRIPTS / "resume_forge.py"),
        "status",
        "--wip",
        str(wip),
        "--json",
        *extra,
    ]
    p = subprocess.run(cmd, capture_output=True, text=True)
    try:
        data = json.loads(p.stdout or "{}")
    except json.JSONDecodeError:
        data = {}
    return p.returncode, data


def _score_wip(wip: Path) -> dict:
    code_c, compact = run_status(wip)
    code_f, full = run_status(wip, "--full")
    cb = len(json.dumps(compact, separators=(",", ":")))
    fb = len(json.dumps(full, separators=(",", ":")))
    ratio = (cb / fb) if fb else 1.0
    has_ids = bool(compact.get("chosen_ids"))
    has_progress = isinstance(compact.get("progress"), dict)
    has_hint = bool(compact.get("resume_hint"))
    no_full_blob = "chosen_n_full" not in compact
    full_has_blob = "chosen_n_full" in full or (
        isinstance(full.get("chosen_n"), dict) and "chosen" in (full.get("chosen_n") or {})
    )
    checks = {
        "compact_exit_0": code_c == 0,
        "full_exit_0": code_f == 0,
        "has_chosen_ids": has_ids,
        "has_progress": has_progress,
        "has_resume_hint": has_hint,
        "compact_omits_full_blob": no_full_blob,
        "ratio_under_max": ratio <= MAX_RATIO or fb < 8000,
        "compact_under_ceiling": cb <= MAX_COMPACT_BYTES,
        "smaller_than_full": cb < fb,
    }
    passed = sum(1 for v in checks.values() if v)
    total = len(checks)
    return {
        "ok": passed == total,
        "wip": str(wip),
        "compact_bytes": cb,
        "full_bytes": fb,
        "ratio": round(ratio, 4),
        "max_ratio": MAX_RATIO,
        "max_compact_bytes": MAX_COMPACT_BYTES,
        "chosen_ids_n": len(compact.get("chosen_ids") or []),
        "checks": checks,
        "passed": passed,
        "total": total,
        "pass_rate": round(passed / total, 4) if total else 0.0,
        "full_has_blob": full_has_blob,
    }


def score() -> dict:
    wip = next(
        (
            p
            for p in GOOD_WIPS
            if p.is_dir()
            and ((p / "discovery" / "chosen_n.json").is_file() or (p / "discovery" / "chosen.json").is_file())
        ),
        None,
    )
    if wip:
        return _score_wip(wip)
    with tempfile.TemporaryDirectory() as td:
        return _score_wip(_make_fixture_wip(Path(td)))


def main() -> None:
    values = score()
    sample = {
        "metric_id": "status-pack-bytes",
        "title": "Compact status JSON byte budget vs --full",
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
