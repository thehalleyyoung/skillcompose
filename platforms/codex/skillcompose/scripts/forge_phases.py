#!/usr/bin/env python3
"""Canonical 50-round forge phases for /skillcompose (replaces T1–T5 theme ladder).

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

Formal forge (all 50 rounds, references/forge_formal_methods.md): each round is a step in a
well-defined methods problem — (i) improve a named desired-output property φ on a concrete task,
and (ii) expand coverage of a discrete task chart θ(X) so the skill is not tuned to one cell of
possible user requests. task_space.py registers coords+phi every round; forge_round.sh refuses
non-novel cells (unless the chart is saturated and phi is new).

Outcome contract (rounds 11–50, outcome_round.py): every round runs the composed skill on a real
domain task before and after its change and keeps both outputs (plus task_coords.json). The forge
exists to improve what the skill produces for its user. Work on the package's own checkers, evals
and metrics is instrumentation; at most 20% of rounds may be mostly instrumentation.

Contract ratchet (every round, concrete_term.py): the theory's obligations are checked on the term the
package actually runs (the scripts SKILL.md invokes, the scripts they call, the writes they make), not
only on the abstract wiring graph. No round may raise the contract potential Φ_c or any component of the
vector Lyapunov debt; P1-unify must bring Φ_c to 0 and every later round must keep it there.

Scheduling: each round is its own agent prompt, spaced ROUND_INTERVAL_SEC (90) apart.
Do not batch multiple forge rounds in one turn.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from outcome_round import OUTCOME_FROM_ROUND  # noqa: E402

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
            "cross-refs, emergent pipeline capability. Strictly more than juxtaposed parts. "
            "Make the concrete term satisfy the hybrid contract: every script SKILL.md runs exists and is "
            "called with flags it declares, nothing writes before the projector, a read-only gate runs after "
            "the last mutator, and every carrier script is reachable. "
            "Each unify round registers a novel task_space obligation cell (coords.obligation + phi) so "
            "P1 expands the space of package properties closed, not the same dead-carrier fix ten times."
        ),
        "done_when": (
            "unify_wholeness predicates pass (or are within one round of PASS), concrete_term.py check "
            "reports Φ_c = 0 by round 10, and task_space coverage shows distinct unify obligation cells"
        ),
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
            "Make the skill's output better on a **new task-chart cell**. Each round: register novel "
            "coords+phi, run the skill on a real domain task, read the output as a demanding reader, "
            "pick its worst flaw against phi, change the skill so the flaw stops, and rerun the same task. "
            "A new check only counts if it changes what gets written, not if it only reports on it."
        ),
        "done_when": (
            "each round's after output beats its before on the named phi (outcome_round.py) and "
            "task_space.py reports novel cells across the phase"
        ),
        "surfaces_planned": ["procedure", "code", "docs", "ux"],
        "outcome_required": True,
        "unify": False,
    },
    {
        "id": "P3-metrics",
        "kind": "metrics",
        "title": "Undeniable reproducible metrics of the output (+ fix when not best)",
        "rounds": [21, 44],
        "n_rounds": 24,
        "job": (
            "Produce non-falsified, reproducible metrics that the skill's outputs are best in some stated "
            "way on **held-out chart cells**: run it and a baseline on tasks whose coords are novel vs "
            "enhance-phase coverage, score with a domain reader rubric, and treat phi as the criterion "
            "under test. Where it loses, write why, fix the skill, and rerun. Measuring the accuracy "
            "of the package's own checkers is instrumentation: allowed, but at most 1 round in 5."
        ),
        "done_when": (
            "METRICS.md scores outputs with reproducible command, baseline, result; task_space coverage "
            "keeps expanding (or new phis after saturation); 'best in X' is about output on covered cells"
        ),
        "surfaces_planned": ["proof", "code", "docs"],
        "outcome_required": True,
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
            "found without this tool. Each round still registers task_space coords+phi; before/after "
            "is the artifact stretch itself. Prefer cells and phis not exhausted in metrics."
        ),
        "done_when": (
            "AWESOME_PROOF.md cites artifact path or public bug URL + confidence + necessity; "
            "task_space coverage audit PASS"
        ),
        "surfaces_planned": ["proof", "procedure", "docs"],
        "outcome_required": True,
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
        "schema": "skillcompose.forge_phases.v2",
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
        "note": (
            "Replaces legacy T1–T5. Ranges: 1–10 unify, 11–20 enhance, 21–44 metrics, 45–50 awesome. "
            "All rounds obey forge_formal_methods.md (desired-output improve + task-space expand)."
        ),
        "formal_methods": "references/forge_formal_methods.md",
    }


def kind_for_round(r: int) -> str:
    p = phase_for_round(r)
    return str(p["kind"]) if p else "unknown"


def _domain(wip: str) -> str:
    """The user's domain from the WIP args (the discovery query), for the outcome loop's reader."""
    for rel in ("discovery/args.json", "args.json"):
        try:
            args = json.loads((Path(wip) / rel).read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            continue
        if isinstance(args, dict):
            for k in ("query", "domain"):
                if isinstance(args.get(k), str) and args[k].strip():
                    return args[k].strip()
    return "the skill's domain"


def round_prompt(wip: str, fork: str, round_n: int, total: int = FORGE_ROUNDS) -> dict[str, Any]:
    """Build the standalone agent prompt payload for one forge round."""
    phase = phase_for_round(round_n)
    if not phase:
        raise SystemExit(f"no phase for round {round_n}")
    kind = phase["kind"]
    theme = phase["id"]
    domain = _domain(wip)
    taskspace = (
        f"TASK SPACE (required every round; forge_formal_methods.md):\n"
        f"- Ensure atlas: python3 $SCRIPTS/task_space.py init-atlas --fork \"$FORK_DIR\" --domain <domain>\n"
        f"- Register a **novel** chart cell + desired property phi for this round:\n"
        f"  python3 $SCRIPTS/task_space.py register --fork \"$FORK_DIR\" --round {round_n} "
        f"--coords '<json>' --phi '<property>' --task-summary '<one line>'\n"
        f"- Rounds 1–10: coords must include obligation=… (unify cell). "
        f"Rounds ≥11: include domain axes (time/place/…). "
        f"Repeating a cell is refused unless the chart is saturated and phi is new.\n"
    )
    outcome = ""
    if round_n >= OUTCOME_FROM_ROUND:
        outcome = (
            f"OUTCOME LOOP (required; forge_round.sh refuses the round without it):\n"
            f"1. python3 $SCRIPTS/outcome_round.py init --fork \"$FORK_DIR\" --round {round_n} "
            f"--task \"<a request a real {domain} user would make>\"\n"
            f"2. Register task_coords (above) so phi matches verdict.phi.\n"
            f"3. Run the skill on that task as the user would; save its output as forge/outcomes/r{round_n:02d}/before.<ext>.\n"
            f"4. Read it as a demanding reader of {domain}. Name its single worst flaw against phi and quote it in verdict.json. "
            f"The flaw is in the output, not in the package's checkers, evals or metrics.\n"
            f"5. Change the skill so that flaw stops happening: procedure, member guidance, references, templates, "
            f"or the scripts the skill runs while producing output.\n"
            f"6. Rerun the same task; save after.<ext>; fill verdict.json honestly (same or worse are logged as misses).\n"
            f"At most 1 round in 5 may spend most of its change on evals/metrics/tests.\n"
        )
    zero = round_n > 10
    contract = (
        f"CONTRACT (forge_round.sh runs the ratchet and refuses a regression):\n"
        f"- Before committing: python3 $SCRIPTS/concrete_term.py check --package \"$FORK_DIR\" "
        f"and fix every obligation this round introduced"
        f"{' (Φ_c must be 0 after the commit)' if zero else ' (Φ_c may not rise; drive it to 0 by round 10)'}.\n"
        f"- If you add, remove or rewire a script, or change how SKILL.md invokes one, refresh the term with "
        f"python3 $SCRIPTS/concrete_term.py write --package \"$FORK_DIR\" and commit references/concrete_term.json.\n"
        f"- A new script SKILL.md runs needs argparse flags that match its invocation; a script that writes "
        f"files is a mutator and must run after the projector and before the final read-only gate.\n"
    )
    text = (
        f"/skillcompose forge-round {round_n}/{total}\n"
        f"WIP_DIR={wip}\n"
        f"FORK_DIR={fork}\n"
        f"PHASE={theme} kind={kind} rounds={phase['rounds'][0]}–{phase['rounds'][1]}\n"
        f"DOMAIN: {domain}\n"
        f"JOB: {phase['job']}\n"
        f"DONE_WHEN: {phase['done_when']}\n"
        f"{contract}"
        f"{taskspace}"
        f"{outcome}"
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
        "sentinel": f"AGENT_LOOP_TICK_skillcompose_forge_r{round_n}",
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
