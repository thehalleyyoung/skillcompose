#!/usr/bin/env python3
"""Canonical 50-round forge phases for /skillremix (replaces T1–T5 theme ladder).

Phases (inclusive):
  1–10   unify    — unified whole strictly more than the sum of its parts
  11–20  enhance  — focused, enhanced abilities beyond unification
  21–44  metrics  — undeniable, reproducible, non-falsified best-in-some-way metrics;
                    when not best, reflect why and fix until the claim holds or is narrowed honestly
                    (user range “21–45”; round 45 starts awesome)
  45–50  awesome  — ship a real awesome proof:
                    • creative domains: actually build the thing (e.g. a novel)
                    • verification domains: find a real third-party bug on GitHub/Bitbucket/etc.
                      you are ≥99% confident is real and that your tool was necessary to find

Scheduling: each round is its own agent prompt, spaced ROUND_INTERVAL_SEC (90) apart.
Do not batch multiple forge rounds in one turn.
"""
from __future__ import annotations

import json
from typing import Any

FORGE_ROUNDS = 50
MIN_CHARS_PER_ROUND = 1000
ROUND_INTERVAL_SEC = 90

PHASES: list[dict[str, Any]] = [
    {
        "id": "P1-unify",
        "kind": "unify",
        "title": "Unification — more than the sum of its parts",
        "rounds": [1, 10],
        "n_rounds": 10,
        "job": (
            "Wire members/surfaces into one coherent whole: shared handoff, verify-before-done, "
            "cross-refs, emergent pipeline capability. Strictly more than juxtaposed parts."
        ),
        "done_when": "unify_wholeness predicates pass (or are within one round of PASS)",
        "surfaces_planned": ["procedure", "code", "proof", "docs"],
        "unify": True,
    },
    {
        "id": "P2-enhance",
        "kind": "enhance",
        "title": "Focused enhanced abilities",
        "rounds": [11, 20],
        "n_rounds": 10,
        "job": (
            "Add sharp, user-facing capabilities that the unified whole enables — depth vs neighbors, "
            "operator UX, domain leverage — not more glue for glue's sake."
        ),
        "done_when": "≥1 enhanced ability demonstrably changes outcome vs incumbent/neighbors",
        "surfaces_planned": ["procedure", "code", "docs", "ux"],
        "unify": False,
    },
    {
        "id": "P3-metrics",
        "kind": "metrics",
        "title": "Undeniable reproducible metrics (+ fix when not best)",
        "rounds": [21, 44],
        "n_rounds": 24,
        "job": (
            "Produce non-falsified, reproducible metrics that the package is best in some stated way. "
            "If a run fails to outperform the baseline, write why, then fix the product or narrow the "
            "claim until the metric is honest and reproducible. Spend this long window iterating claims."
        ),
        "done_when": (
            "METRICS.md (or evals card) has a reproducible command, baseline, result, and either "
            "a held 'best in X' claim or a documented fix loop that restored the claim"
        ),
        "surfaces_planned": ["proof", "code", "docs"],
        "unify": False,
    },
    {
        "id": "P4-awesome",
        "kind": "awesome",
        "title": "Awesome real-world proof",
        "rounds": [45, 50],
        "n_rounds": 6,
        "job": (
            "Actually build something awesome with the skill — e.g. a finished novel for writing — "
            "OR, for verification tools, discover a bug in someone else's public repo "
            "(GitHub/Bitbucket/etc.) you are ≥99% confident is real and that could not have been "
            "found without this tool."
        ),
        "done_when": "AWESOME_PROOF.md cites the artifact path or public bug URL + confidence + necessity",
        "surfaces_planned": ["proof", "procedure", "docs"],
        "unify": False,
    },
]


def phase_for_round(r: int) -> dict[str, Any] | None:
    for p in PHASES:
        a, b = p["rounds"]
        if a <= r <= b:
            return p
    return None


def phases_doc(gaps: list[dict] | None = None) -> dict[str, Any]:
    """Emit forge_phases.json content, optionally annotating with audit gaps."""
    gap_ids = {g.get("id") for g in (gaps or []) if g.get("id")}
    phases = []
    for p in PHASES:
        item = dict(p)
        item["linked_gap_ids"] = sorted(gap_ids)[:8] if gap_ids else []
        item["success_signal"] = item["done_when"]
        phases.append(item)
    return {
        "schema": "skillremix.forge_phases.v2",
        "forge_rounds": FORGE_ROUNDS,
        "min_chars_per_round": MIN_CHARS_PER_ROUND,
        "round_interval_sec": ROUND_INTERVAL_SEC,
        "phases": phases,
        "scheduling": (
            f"Each forge round is its own agent prompt. In Antigravity, after round r logs PASS, "
            f"arm a one-shot schedule timer (DurationSeconds={ROUND_INTERVAL_SEC}) with the round r+1 prompt "
            f"and end the turn immediately (never use shell sleep). Acquire agent_busy.lock at round start; "
            f"defer if still busy. (Legacy Cursor/CLI fallback: schedule_forge_loop.sh with notify_on_output.)"
        ),
        "note": "Replaces legacy T1–T5. Ranges: 1–10 unify, 11–20 enhance, 21–44 metrics, 45–50 awesome.",
    }


def kind_for_round(r: int) -> str:
    p = phase_for_round(r)
    return str(p["kind"]) if p else "unknown"


def round_prompt(wip: str, fork: str, round_n: int, total: int = FORGE_ROUNDS) -> dict[str, Any]:
    """Build the standalone agent prompt payload for one forge round."""
    phase = phase_for_round(round_n)
    if not phase:
        raise SystemExit(f"no phase for round {round_n}")
    kind = phase["kind"]
    theme = phase["id"]
    text = (
        f"/skillremix forge-round {round_n}/{total}\n"
        f"WIP_DIR={wip}\n"
        f"FORK_DIR={fork}\n"
        f"PHASE={theme} kind={kind} rounds={phase['rounds'][0]}–{phase['rounds'][1]}\n"
        f"JOB: {phase['job']}\n"
        f"DONE_WHEN: {phase['done_when']}\n"
        f"REQUIREMENTS:\n"
        f"- This turn does EXACTLY round {round_n} — do not start round {round_n + 1}.\n"
        f"- Multi-surface leap (≥3 of procedure/code/proof/docs/ux).\n"
        f"- ≥{MIN_CHARS_PER_ROUND} product chars (forge logs excluded); one git commit "
        f"`forge({round_n}/{total}): {theme} — <gap>`.\n"
        f"- Log via forge_round.sh with --kind {kind}.\n"
        f"- After logging PASS, arm the next round wake in {ROUND_INTERVAL_SEC}s via "
        f"Antigravity's native `schedule` tool (`DurationSeconds: {ROUND_INTERVAL_SEC}`, `Prompt`: round {round_n + 1} prompt from forge_phases.py) "
        f"and end the turn immediately (never shell sleep; legacy Cursor fallback: schedule_forge_loop.sh). "
        f"Acquire agent_busy at round start; if busy on wake, defer 15s via `schedule`.\n"
        f"- Do not continue forging in this turn.\n"
        f"- If round {round_n} == {total}, run ship_check instead of scheduling another round."
    )
    return {
        "round": round_n,
        "total": total,
        "kind": kind,
        "theme": theme,
        "interval_sec": ROUND_INTERVAL_SEC,
        "wip": wip,
        "fork": fork,
        "prompt": text,
        "sentinel": f"AGENT_LOOP_TICK_skillremix_forge_r{round_n}",
    }


def validate_log_phases(rows: list[dict], rounds: int = FORGE_ROUNDS) -> dict[str, Any]:
    """Require each logged round's kind/theme to match the canonical phase."""
    by_round = {int(r["round"]): r for r in rows if "round" in r}
    reasons: list[str] = []
    coverage: dict[str, int] = {p["id"]: 0 for p in PHASES}
    for i in range(1, rounds + 1):
        expect = phase_for_round(i)
        if not expect:
            continue
        row = by_round.get(i)
        if not row:
            continue
        kind = str(row.get("kind") or "").lower()
        theme = str(row.get("theme") or "").lower()
        want = expect["kind"]
        ok = kind == want or want in theme or expect["id"].lower() in theme
        if want == "unify":
            ok = ok or row.get("unify") is True or kind in {"unify", "subskill", "superskill"}
        if not ok:
            reasons.append(
                f"round {i}: expected kind={want!r} (phase {expect['id']}), "
                f"got kind={kind!r} theme={row.get('theme')!r}"
            )
        else:
            coverage[expect["id"]] += 1

    for p in PHASES:
        a, b = p["rounds"]
        need = b - a + 1
        present = sum(1 for i in range(a, b + 1) if i in by_round)
        if present >= need and coverage[p["id"]] < need:
            reasons.append(f"phase {p['id']} has {coverage[p['id']]}/{need} correctly tagged rounds")
        elif present < need:
            reasons.append(f"phase {p['id']} incomplete: {present}/{need} rounds present")

    return {
        "decision": "PASS" if not reasons else "FAIL",
        "coverage": coverage,
        "reasons": reasons,
        "phases": [{"id": p["id"], "rounds": p["rounds"], "kind": p["kind"]} for p in PHASES],
        "round_interval_sec": ROUND_INTERVAL_SEC,
    }


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", help="Write forge_phases.json")
    ap.add_argument("--round", type=int, help="Print phase for this round")
    ap.add_argument("--prompt-round", type=int, help="Emit standalone forge-round prompt JSON")
    ap.add_argument("--wip", default="", help="WIP_DIR for --prompt-round")
    ap.add_argument("--fork", default="", help="FORK_DIR for --prompt-round")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    if args.prompt_round is not None:
        out = round_prompt(args.wip, args.fork, args.prompt_round)
        print(json.dumps(out, indent=2) if args.json else out["prompt"])
        return 0
    if args.round is not None:
        p = phase_for_round(args.round)
        print(json.dumps(p, indent=2) if args.json else p)
        return 0 if p else 1
    doc = phases_doc()
    if args.out:
        from pathlib import Path

        path = Path(args.out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(doc, indent=2) if args.json else doc)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
