# Strict wholeness (more than the sum of parts)

`/skillremix` remix packages **must not ship** as a folder of upgraded skills glued by a thin router. `unify_wholeness.py` + `ship_check.py` FAIL until every predicate below is true.

P1 (rounds **1–10**) is dedicated to making this true. Later phases assume it holds.

## Definition

A package is **strictly more than the sum of its parts** iff **all** hold:

| # | Predicate | Hard evidence |
|---|---|---|
| 1 | `shared_contract` | `references/` or `subskills/` handoff schema (`handoff*`, `pipeline_pack`, `phase_handoff`, …) |
| 2 | `shared_verify` | Verify-gate script/subskill with verify/false-done behavior |
| 3 | `superskill_requires_verify` | Package `SKILL.md` requires verify-gate **before** claiming done |
| 4 | `superskill_wiring` | Superskill names member skills + subskills (phases, not a mashup blurb) |
| 5 | `cross_member_refs` | ≥2 member `skills/*/SKILL.md` reference the shared handoff/contract |
| 6 | `emergent_eval` | `evals/` \| `scripts/` \| `references/` file names ≥2 members **and** asserts pipeline/e2e/wholeness |
| 7 | `wholeness_doc` | `WHOLENESS.md` or `REMIX_PLAN.md` `## Wholeness` covering handoff, verify, emergent claim, cross-wire |
| 8 | `not_wrapper_only` | Superskill body ≥2000 chars with handoff/verify/phase/false-done substance |
| 9 | `no_juxtaposition` | Shared `references\|scripts\|subskills` exist **and** cross-member refs hold |
| 10 | `forge_unify_mass` | **50** rounds, each ≥1000 product chars, unique commits; **rounds 1–10** tagged `unify` |

If any predicate fails, decision is **FAIL**. There is no “mostly unified” soft pass.

## Also required for ship (P3 / P4)

These are enforced by `ship_check.py` (not only wholeness):

- **`METRICS.md`** — reproducible command, baseline, results; fix/narrow loop if not best
- **`AWESOME_PROOF.md`** — real artifact (e.g. novel) **or** public third-party bug URL with ≥99% confidence + necessity

## Reject (automatic FAIL)

- Side-by-side `-upgraded` forks with a superskill that only says “call A then B”
- Renamed copies of members as “subskills” with no I/O contract
- Padding whitespace / duplicate dumps to hit 1000 chars
- One commit labeled as many forge rounds
- Verify mentioned in README only, never required before done
- Fake “metrics” without a runnable command
- Awesome proof that is only a plan, not a built artifact / filed bug

## Agent loop implication

Spend rounds **1–10** driving every predicate FAIL→PASS. **Done is `ship_check.py` PASS**, not “we finished 50 chats in one turn.”
