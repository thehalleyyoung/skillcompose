# Per-round protocol (50 real rounds × ≥1000 chars × 90s spacing)

Nominal chat summaries do **not** count. Ship fails unless the forge log proves **50 separate commits**, each with **≥1000 characters** of product churn, tagged to the correct phase, each executed as **its own prompt** spaced **90 seconds** from the next.

## Formal methods framing (all 50 rounds)

Every round is one step of the problem in [`forge_formal_methods.md`](forge_formal_methods.md):

1. **Contract ratchet** — \(\Phi_c\) and debt vector must not rise (`concrete_term.py`).
2. **Task-space expansion** — register novel chart coordinates (+ new \(\varphi\) after saturation) via `task_space.py`.
3. **Desired-output improvement** — rounds ≥11: before/after evidence on that task for property \(\varphi\); rounds 1–10: close the named unify obligation cell.

`forge_round.sh` refuses a round that fails (1) or (2); from round 11 it also refuses a round that fails (3).

## Phase map

| Rounds | `kind` | Focus |
|---|---|---|
| 1–10 | `unify` | Unified whole **more than the sum of its parts** + novel obligation cells |
| 11–20 | `enhance` | Better output on **new** task-chart cells (outcome + task_space) |
| 21–44 | `metrics` | Held-out cells vs baseline; expand coverage; fix until best on \(\varphi\) |
| 45–50 | `awesome` | Real awesome proof on registered cells/\(\varphi\) |

## Outcome contract (rounds 11–50, mandatory)

A forge drifts when each round improves the package's view of itself: a checker, an eval for the checker, a metric about the eval. The user's output never changes. From round 11 every round is anchored in output:

0. Ensure `forge/task_space/atlas.json` exists (`task_space.py init-atlas`). Register novel `--coords` + `--phi` for this round (`task_space.py register`) so `forge/outcomes/rNN/task_coords.json` exists.
1. `outcome_round.py init --fork "$FORK_DIR" --round R --task "<a request a real user of the domain would make>"`.
2. Run the skill on the task as that user would. Save the output as `forge/outcomes/rNN/before.<ext>`.
3. Read it as a demanding reader of the domain. In `verdict.json`, name its single worst flaw against \(\varphi\`, quote it verbatim (`before_excerpt`), and set `phi` to match `task_coords.phi`. The flaw is in the output, not in the package's checkers, evals or metrics.
4. Change the skill so the flaw stops happening: procedure, member guidance, references, templates, or the scripts the skill runs while producing output.
5. Rerun the same task. Save `after.<ext>`, quote where the flaw is fixed (`after_excerpt`), and set `verdict` to `better`, `same` or `worse`. Same and worse are logged as misses.

`forge_round.sh` runs `outcome_round.py check` and refuses the round if the files are missing, the output did not change, or an excerpt is not in its file. Each round's changed characters are split into skill, instrumentation (evals/, tests/, metrics/, METRICS.md, WHOLENESS.md, gold labels, forge logs) and output. Validation fails when more than 20% of rounds are mostly instrumentation, or when fewer than half the rounds made the output better. The outputs themselves do not count toward the 1000 product characters.

## Contract ratchet (every round)

The guarantees of `theory.md` §4.1 are checked on the term the package actually runs, read by `scripts/concrete_term.py` from the scripts `SKILL.md` invokes, their callees, and their writes and exit codes. Each failed obligation adds 1 to the contract potential $\Phi_c$:

- an invoked script is missing;
- a flag is undeclared, or a required flag is omitted;
- there is no gate that can fail, or the projector cannot abstain;
- a gate writes;
- a mutator runs after the last gate, or before the projector;
- a carried member script was removed;
- a composed argument is no longer named in `SKILL.md`.

Before committing, run `concrete_term.py check --package "$FORK_DIR"`. When scripts or their invocations change, refresh `references/concrete_term.json` with `concrete_term.py write`.

`forge_round.sh` runs `concrete_term.py ratchet --base HEAD~1 --head HEAD` and refuses the round if $\Phi_c$ rose or any component of the Lyapunov debt vector rose. The scalar sum is not enough, because paying a downstream debt can hide an upstream regression. From round 11, it also refuses unless $\Phi_c = 0$ and the artifact is current. `forge_log.py validate --fork` recomputes the ratchet from the commits for rounds logged without it.

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
task_space.init-atlas (once); task_space.register(novel coords + phi)
if r >= 11: outcome_round.py init; run skill → before; name worst flaw vs phi
implement (change the skill) → if r >= 11: rerun → after, verdict.phi
concrete_term.py write; concrete_term.py check   # Φ_c must not rise; 0 from round 11
commit forge(r/50) → forge_round.sh  # task_space + contract + outcome, releases busy
if r < 50:
  prompt = forge_phases.py --prompt-round (r+1)
  schedule(DurationSeconds=90, Prompt=prompt)
  end turn immediately (stop forging this turn)
else: ship_check  # includes task_space coverage audit
```

## Validate before ship

```bash
python3 scripts/forge_log.py validate --log …/usefulness_forge.jsonl --rounds 50 --min-chars 1000 --strict-phases --fork "$PKG_DIR" --json
python3 scripts/outcome_round.py audit --fork "$PKG_DIR" --log …/usefulness_forge.jsonl --json
python3 scripts/check_phases.py --log …/usefulness_forge.jsonl --rounds 50 --json
python3 scripts/unify_wholeness.py --package "$PKG_DIR" --rounds 50 --min-chars 1000 --json
python3 scripts/concrete_term.py check --package "$PKG_DIR" --require-artifact --json
python3 scripts/ship_check.py --fork "$PKG_DIR" --rounds 50 --min-chars 1000 --json
```
