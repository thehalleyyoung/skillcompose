#!/usr/bin/env python3
"""Measure remix coherence gate catch rate on fixtures."""

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
FIX = ROOT / "fixtures"
BAD = Path("/Users/halley/Documents/linkedin-1/skillremix-wip-20260721T000909Z/discovery/chosen_n.json")


def run_gate(chosen: Path, query: str, domain: str) -> dict:
    p = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "remix_coherence_gate.py"),
            "--chosen-n",
            str(chosen),
            "--query",
            query,
            "--domain",
            domain,
            "--json",
        ],
        capture_output=True,
        text=True,
    )
    try:
        data = json.loads(p.stdout or "{}")
    except json.JSONDecodeError:
        data = {"ok": None, "raw": (p.stdout or p.stderr)[:200]}
    data["_exit"] = p.returncode
    return data


def score() -> dict:
    FIX.mkdir(parents=True, exist_ok=True)
    # Ensure a clean fixture (lit-review only)
    clean = {
        "chosen": [
            {
                "id": "bytedance/deer-flow@systematic-literature-review",
                "query": "literature review",
                "github_description": "systematic literature review skill",
                "discovery_role": "domain_core",
            },
            {
                "id": "example/research@arxiv-search",
                "query": "arxiv search",
                "github_description": "search arxiv papers for research",
                "discovery_role": "domain_core",
            },
            {
                "id": "example/evals@eval-harness-first",
                "query": "eval harness",
                "github_description": "evaluation harness first",
                "discovery_role": "practice_support",
            },
        ],
        "ids": [],
    }
    clean_path = FIX / "chosen_n_clean.json"
    clean_path.write_text(json.dumps(clean, indent=2), encoding="utf-8")

    writing_false = FIX / "chosen_n_writing_false.json"
    writing_clean = FIX / "chosen_n_writing_clean.json"

    cases = []
    if BAD.is_file():
        bad = run_gate(BAD, "literature review", "research")
        caught = bad.get("ok") is False and bad.get("_exit") == 2
        spring = any(
            "springboot" in str(w.get("id", "")).lower() or w.get("off_domain_hits")
            for w in (bad.get("weak") or [])
        )
        cases.append({"name": "uc03_bad_catch", "ok": caught and spring, "detail": bad.get("weak")})
    else:
        # Fixture-local springboot stand-in when external WIP missing
        spring_fix = FIX / "chosen_n_springboot.json"
        spring_fix.write_text(
            json.dumps(
                {
                    "chosen": [
                        {
                            "id": "affaan-m/everything-claude-code@springboot-verification",
                            "query": "literature review",
                            "github_description": "springboot verification helpers",
                            "discovery_role": "practice_support",
                        }
                    ]
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        bad = run_gate(spring_fix, "literature review", "research")
        caught = bad.get("ok") is False and bad.get("_exit") == 2
        cases.append({"name": "uc03_bad_catch", "ok": caught, "detail": bad.get("weak")})

    good = run_gate(clean_path, "literature review", "research")
    cases.append({"name": "clean_pass", "ok": good.get("ok") is True and good.get("_exit") == 0})

    if writing_false.is_file():
        wf = run_gate(writing_false, "", "writing")
        weak_ids = " ".join(w.get("id") or "" for w in (wf.get("weak") or []))
        caught_sb = "storybook" in weak_ids.lower() or "react-native" in weak_ids.lower()
        caught_nv = "skillspector" in weak_ids.lower() or "nvidia" in weak_ids.lower()
        cases.append(
            {
                "name": "writing_false_pass_catch",
                "ok": wf.get("ok") is False and wf.get("_exit") == 2 and caught_sb and caught_nv,
                "detail": wf.get("weak"),
            }
        )
    else:
        cases.append({"name": "writing_false_pass_catch", "ok": False, "detail": "missing fixture"})

    if writing_clean.is_file():
        wc = run_gate(writing_clean, "creative writing", "writing")
        cases.append(
            {
                "name": "writing_clean_pass",
                "ok": wc.get("ok") is True and wc.get("_exit") == 0,
                "detail": wc.get("members"),
            }
        )
    else:
        cases.append({"name": "writing_clean_pass", "ok": False, "detail": "missing fixture"})

    passed = sum(1 for c in cases if c["ok"])
    return {
        "cases": cases,
        "passed": passed,
        "total": len(cases),
        "catch_rate": round(passed / len(cases), 4) if cases else 0.0,
        "pass_rate": round(passed / len(cases), 4) if cases else 0.0,
    }


def main() -> None:
    values = score()
    sample = {
        "metric_id": "remix-coherence",
        "title": "Remix coherence gate catch rate on fixtures",
        "at": datetime.now(tz=timezone.utc).isoformat(),
        "ts": time.time(),
        "values": values,
    }
    with (ROOT / "history.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(sample) + "\n")
    (ROOT / "latest.json").write_text(json.dumps(sample, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "values": values}))


if __name__ == "__main__":
    main()
