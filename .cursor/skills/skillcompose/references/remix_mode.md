# Remix mode (`--n N`)

When the user passes **`--n N`** (N ≥ 2), `/skillremix` does **not** upgrade a single skill in isolation. It builds an **end-to-end skill system**, then forges on the **fixed 50-round phase plan** (T1–T5 retired):

1. Discover an eligible pool (adoption floor; highly popular allowed).
   - Domain-exact queries for `--domain`.
   - When **`--n` is large (≥5)**: also search **practice-support** skills — capabilities necessary to *practice* the domain end-to-end (verify, evals, continuity, research, git, …), even if those skills are not only about that domain.
2. Pick **N complementary** skills (`pick_n_eligible.py`, with practice-role mix when N is large).
3. Clone + audit each; score which gaps would break composition.
4. **Decide buffs** — which members need heavy/medium/light investment inside P1–P2.
5. Propose **subskills** + one **superskill**.
6. Execute **50 real forge rounds** (one prompt each, **90s** apart) (≥1000 chars + own commit each):
   - **1–10 unify** — more than the sum of parts → `unify_wholeness` PASS
   - **11–20 enhance** — focused enhanced abilities
   - **21–44 metrics** — undeniable reproducible metrics; fix when not best
   - **45–50 awesome** — real novel/artifact **or** ≥99%-confident third-party bug find
7. `ship_check` PASS → dual-install.

## Why this exists

Marketplace skills are often **phase-local**. Users want a **pipeline** that is strictly more than A+B+C in a folder.

## CLI

```text
/skillremix --n 3 --domain writing
/skillremix --n 4 --remix-plan-only
/skillremix --n 2 research verification
```

Incompatible with `--pin` (pin is single-skill upgrade mode).

## Decision rules (buff vs skip-light)

| Signal | Prefer |
|---|---|
| High gap_score (no verify / no scripts / no evals) | **Heavy buff** during P1–P2 |
| Overlaps another member’s job heavily | Prefer one buffed canonical |
| Already strong on I/O + verify | **Light buff** (install UX + non-triggers) |
| Wrong-sense name trap | Non-triggers on superskill; may drop |

## Subskill shapes (good)

- `handoff-pack` — schema + verify between phases
- `verify-gate` — shared false-done prevention
- Domain bridge / `metric-rollup`

## Subskill shapes (reject)

- Renamed copy of a member with no new I/O contract
- “Wrapper” that only says “call skill A then B”

## Superskill requirements

- Explicit phase list wiring buffed members + subskills
- Must run verify-gate before claiming done
- `UPSTREAM.md` / `REMIX_PLAN.md` / `WHOLENESS.md` cite members
- After P3/P4: `METRICS.md` + `AWESOME_PROOF.md`

## Large-N discovery (practice-support)

For `--n ≥ 5` (or `--practice-support on`), `discover_skills.py` expands beyond domain-labeled hits:

| Role | Meaning |
|---|---|
| `domain_core` | Skills found via domain pack queries (e.g. “novel writing”) |
| `practice_support` | Skills you’d need while practicing the domain (verify, continuity, evals, git, research notes, …) — not required to be domain-exclusive |

`pick_n_eligible.py --practice-mix auto` then balances ~half core / half support so a large remix is a real practice pipeline, not N near-duplicate domain skills.

```bash
python3 $SCRIPTS/discover_skills.py --out …/candidates.jsonl --domain writing --n 8 --practice-support auto --json
python3 $SCRIPTS/pick_n_eligible.py --candidates …/enriched.jsonl --n 8 --practice-mix auto --json
```

## Round budget (fixed)

| Rounds | Kind |
|---|---|
| 1–10 | `unify` |
| 11–20 | `enhance` |
| 21–44 | `metrics` |
| 45–50 | `awesome` |

Each round: **own git commit**, **≥1000 chars**, **≥3 surfaces**. Thin/batched/padded rounds do not count.

## Ship gate (strict)

```bash
python3 $SCRIPTS/unify_wholeness.py --package "$PKG_DIR" --rounds 50 --min-chars 1000 --json
python3 $SCRIPTS/ship_check.py --fork "$PKG_DIR" --rounds 50 --min-chars 1000 --json
```

See `references/wholeness.md` + `references/forge_phases.md`.
