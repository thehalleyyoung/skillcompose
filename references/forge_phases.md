# Forge phases (50 rounds) — replaces T1–T5

Every `/skillcompose` run uses this fixed phase plan. **Each round is its own agent prompt**, scheduled **90 seconds** after the previous round completes (never batch 50 rounds in one turn).

**Formal problem (all rounds):** improve a named desired-output property \(\varphi\) on a concrete task **and** expand coverage of a discrete task chart \(\theta(\mathcal{X})\). Full statement: [`forge_formal_methods.md`](forge_formal_methods.md). Executable: `scripts/task_space.py`.

| Rounds | Kind | Job |
|---|---|---|
| **1–10** | `unify` | Unified whole **more than the sum of parts**; each round closes a **novel unify obligation cell** (`coords.obligation`) while driving \(\Phi_c \to 0\). |
| **11–20** | `enhance` | Improve skill **output** on a **new task-chart cell**: before → fix \(\varphi\) → after. |
| **21–44** | `metrics` | Held-out cells + baseline rubric; fix until skill wins on stated \(\varphi\); keep expanding coverage. |
| **45–50** | `awesome` | Artifact-scale proof (novel / ≥99% third-party bug) still on registered coords+\(\varphi\). |

## Outcome contract (rounds 11–50)

The forge is for the skill's user. From round 11, each round keeps the skill's output for one real domain task before and after its change (`forge/outcomes/rNN/`), including `task_coords.json` (chart cell + \(\varphi\)), names the worst flaw in the before output with a verbatim quote, and says honestly whether the after output is better. `scripts/outcome_round.py` scaffolds and checks this, `forge_round.sh` refuses a round without it **and** without a novel task-space registration, and `forge_log.py validate` fails a forge where more than 20% of rounds are mostly evals/metrics/tests or fewer than half improved the output. Work on the package's own checkers is instrumentation: it counts only when it changes what the skill writes. Full rules: [`round_protocol.md`](round_protocol.md).

Every round, including rounds 1–10, also passes the contract ratchet (`scripts/concrete_term.py`, `theory.md` §4.2) **and** `task_space.py check`. The theory's obligations are checked on the scripts the package actually runs. No round may raise the contract potential $\Phi_c$ or any component of the Lyapunov debt vector. Unification must end with $\Phi_c = 0$, and every later round keeps it there, so the composition guarantees hold for the package at every round, not only for the graph emitted at round 0.

## Scheduling (mandatory)

```text
complete round r  →  release busy lock  →  schedule(DurationSeconds=90, Prompt=round r+1)  →  end turn
  → on wakeup: if busy, re-arm 15s & stop  →  else execute round r+1  →  re-arm 90s
```

Helpers:

```bash
python3 scripts/agent_busy.py acquire --wip "$WIP_DIR" --round "$R" --json   # start of round
python3 scripts/task_space.py init-atlas --fork "$FORK_DIR" --domain writing   # once
python3 scripts/forge_phases.py --prompt-round $((R+1)) --wip "$WIP_DIR" --fork "$FORK_DIR" --json
```

In Antigravity, arm ONE next-round wake using the native **`schedule` tool** (`DurationSeconds: 90`, `Prompt`: the `prompt` string from `forge_phases.py --prompt-round $((R+1))`), then end your turn immediately. **Never** use a shell `sleep` command as a timer in Antigravity. (Legacy Cursor/CLI fallback: `scripts/schedule_forge_loop.sh`.) One round per wake; stop after round 50 / `ship_check`.

## Per-round rules

- Own `forge(r/50): …` commit
- ≥1000 product characters (`measure_chars.py`)
- ≥3 surfaces; `radical: true`
- `kind` matches phase (`forge_round.sh` auto-sets)
- `task_space.py register` with novel cell (or new \(\varphi\) after saturation)

## Phase artifacts (ship-blocking)

| Phase | Required evidence |
|---|---|
| P1 unify | `unify_wholeness.py` PASS (remix); \(\Phi_c=0\) |
| P2 enhance | Capabilities in SKILL/scripts; COMPARISON updated |
| P3 metrics | `METRICS.md` with reproducible command, baseline, results, fix-loop if not best |
| P4 awesome | `AWESOME_PROOF.md` with artifact path **or** public bug URL + 99% confidence + necessity |
| All | `forge/task_space/atlas.json` + coverage audit PASS |

## Schema

```json
{
  "schema": "skillcompose.forge_phases.v2",
  "forge_rounds": 50,
  "round_interval_sec": 90,
  "formal_methods": "references/forge_formal_methods.md",
  "phases": [
    {"id": "P1-unify", "kind": "unify", "rounds": [1, 10]},
    {"id": "P2-enhance", "kind": "enhance", "rounds": [11, 20]},
    {"id": "P3-metrics", "kind": "metrics", "rounds": [21, 44]},
    {"id": "P4-awesome", "kind": "awesome", "rounds": [45, 50]}
  ]
}
```
