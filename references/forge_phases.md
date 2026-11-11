# Forge phases (50 rounds) — replaces T1–T5

Every `/skillremix` run uses this fixed phase plan. **Each round is its own agent prompt**, scheduled **90 seconds** after the previous round completes (never batch 50 rounds in one turn).

| Rounds | Kind | Job |
|---|---|---|
| **1–10** | `unify` | Build a unified whole that is **strictly more than the sum of its parts**. |
| **11–20** | `enhance` | Add **focused, enhanced abilities** the unified whole enables. |
| **21–44** | `metrics` | **Undeniable, reproducible, non-falsified** best-in-some-way metrics; if not best, reflect and **fix** (user window “21–45”; round **45** starts awesome). |
| **45–50** | `awesome` | **Actually build something awesome** (e.g. a novel) **or** find a ≥99%-confident real bug in someone else's public repo that needed this tool. |

## Scheduling (mandatory)

```text
complete round r  →  release busy lock  →  schedule(DurationSeconds=90, Prompt=round r+1)  →  end turn
  → on wakeup: if busy, re-arm 15s & stop  →  else execute round r+1  →  re-arm 90s
```

Helpers:

```bash
python3 scripts/agent_busy.py acquire --wip "$WIP_DIR" --round "$R" --json   # start of round
python3 scripts/forge_phases.py --prompt-round $((R+1)) --wip "$WIP_DIR" --fork "$FORK_DIR" --json
```

In Antigravity, arm ONE next-round wake using the native **`schedule` tool** (`DurationSeconds: 90`, `Prompt`: the `prompt` string from `forge_phases.py --prompt-round $((R+1))`), then end your turn immediately. **Never** use a shell `sleep` command as a timer in Antigravity. (Legacy Cursor/CLI fallback: `scripts/schedule_forge_loop.sh`.) One round per wake; stop after round 50 / `ship_check`.

## Per-round rules

- Own `forge(r/50): …` commit
- ≥1000 product characters (`measure_chars.py`)
- ≥3 surfaces; `radical: true`
- `kind` matches phase (`forge_round.sh` auto-sets)

## Phase artifacts (ship-blocking)

| Phase | Required evidence |
|---|---|
| P1 unify | `unify_wholeness.py` PASS (remix) |
| P2 enhance | Capabilities in SKILL/scripts; COMPARISON updated |
| P3 metrics | `METRICS.md` with reproducible command, baseline, results, fix-loop if not best |
| P4 awesome | `AWESOME_PROOF.md` with artifact path **or** public bug URL + 99% confidence + necessity |

## Schema

```json
{
  "schema": "skillremix.forge_phases.v2",
  "forge_rounds": 50,
  "round_interval_sec": 90,
  "phases": [
    {"id": "P1-unify", "kind": "unify", "rounds": [1, 10]},
    {"id": "P2-enhance", "kind": "enhance", "rounds": [11, 20]},
    {"id": "P3-metrics", "kind": "metrics", "rounds": [21, 44]},
    {"id": "P4-awesome", "kind": "awesome", "rounds": [45, 50]}
  ]
}
```
