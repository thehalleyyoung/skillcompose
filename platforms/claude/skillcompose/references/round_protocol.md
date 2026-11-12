# Per-round protocol (50 real rounds × ≥1000 chars × 90s spacing)

Nominal chat summaries do **not** count. Ship fails unless the forge log proves **50 separate commits**, each with **≥1000 characters** of product churn, tagged to the correct phase, each executed as **its own prompt** spaced **90 seconds** from the next.

## Phase map

| Rounds | `kind` | Focus |
|---|---|---|
| 1–10 | `unify` | Unified whole **more than the sum of its parts** |
| 11–20 | `enhance` | Focused enhanced abilities |
| 21–44 | `metrics` | Undeniable reproducible metrics; reflect + fix when not best |
| 45–50 | `awesome` | Real awesome proof (novel / artifact) or ≥99%-confident third-party bug |

## One prompt per round (mandatory)

**Forbidden:** running rounds 1–N in a single agent turn.

**Required:**

1. `agent_busy.py acquire` then run **exactly one** forge round in this turn.
2. Commit + `forge_round.sh` (refuses if <1000 chars; releases busy lock).
3. **Wake the agent** for the next round **90 seconds** later:
   - **In Antigravity (mandatory):** generate the round `r+1` prompt with `python3 scripts/forge_phases.py --prompt-round $((r+1)) --wip "$WIP_DIR" --fork "$FORK_DIR" --json`, then call the native **`schedule` tool** (`DurationSeconds: 90`, `Prompt: <prompt>`) and **end your turn immediately** (call no more tools). **Never** use a shell `sleep` command as a timer in Antigravity.
   - *(Legacy Cursor/CLI fallback only when `schedule` tool is unavailable: `schedule_forge_loop.sh --from $((r+1)) --to $((r+1)) --interval 90` with Shell `notify_on_output`.)*
4. On timer wake: check `agent_busy.py check --wip "$WIP_DIR"` first — if still busy (exit `0`), re-arm `schedule(DurationSeconds=15)` and end the turn. Otherwise read `resume_forge.py next`, execute **only** that round, and re-arm `schedule(DurationSeconds=90)` until round 50; then run `ship_check`.

## Loop skeleton

```text
r = resume_forge.py next
agent_busy.acquire(r)
# THIS TURN: only r
implement → commit forge(r/50) → forge_round.sh  # releases busy
if r < 50:
  prompt = forge_phases.py --prompt-round (r+1)
  schedule(DurationSeconds=90, Prompt=prompt)
  end turn immediately (stop forging this turn)
else: ship_check
```

## Validate before ship

```bash
python3 scripts/forge_log.py validate --log …/usefulness_forge.jsonl --rounds 50 --min-chars 1000 --strict-phases --json
python3 scripts/check_phases.py --log …/usefulness_forge.jsonl --rounds 50 --json
python3 scripts/unify_wholeness.py --package "$PKG_DIR" --rounds 50 --min-chars 1000 --json
python3 scripts/ship_check.py --fork "$PKG_DIR" --rounds 50 --min-chars 1000 --json
```
