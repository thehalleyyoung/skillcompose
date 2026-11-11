# 7-Family Generative Skill Manifold Benchmark (`agy` + Sonnet 5.5 Blind Judge)

This benchmark suite evaluates three skill-composition regimes constructed from the **exact same 4 upstream member skills** per task family, calling the solver agent **strictly once per `(task_family, regime)`** (`7 × 3 = 21` isolated runs) and evaluating anonymized outputs with **Sonnet 5.5** (`claude-sonnet-5-5`) as blind judge alongside deterministic exogenous `oracle.py` verifiers.

## Composition Regimes Held Under Test

Every family compiles its `.agents/skills/<skill_name>/` bundle from identical member `SKILL.md` files under three regimes:

1. **`concat` ($\bigwedge_{i=1}^4 s_i$ — Naive Prompt Concatenation):** Concatenates all 4 member `SKILL.md` bodies verbatim into one prompt without fiber projection, Galois conormal precedence, or sheaf cocycle verification.
2. **`union` ($\bigcup_{i=1}^4 s_i$ — Skill Union Router):** Installs an explicit skill-union router over `./members/<slug>.md` that selects the single closest member skill and executes it faithfully without mixing sibling instructions.
3. **`manifold` ($\mathfrak{G}_{\mathcal{M}}$ — Lawvere–Amari Generative Skill Manifold):** Mechanically compiled by `scripts/compose_skills.py` with executable Stage 1 inverse-chart + Fisher–Rao projection (`scripts/project_manifold.py`), Galois conormal invariant core $\Phi_{\text{core}}$, and Stage 3 dominator + Čech sheaf gluing gate (`scripts/verify_dominator_gate.py --glue`).

## The 7 Concrete Task Families

| # | Family ID | Domain | 4 Member Skills Combined | Core Recombinant & Logical Tension |
|---|---|---|---|---|
| 1 | `f1_streaming_sql_sheaf` | `data` | JSONL stream parser + SQLite transactional migrator + API contract emitter + SHA-256 audit manifest | Constant-memory line streaming + malformed quarantine vs single atomic `orders_v2` SQLite transaction + coupled `api_contract.json` $\leftrightarrow$ `migration_manifest.json` sheaf keys |
| 2 | `f2_kleene_policy_compiler` | `automation` | Recursive-descent `NOT > AND > OR` parser + Kleene $K_3$ evaluator + AST serializer + truth-table auditor | Operator precedence (`OR` vs `AND` binding) + strong Kleene 3-valued logic (`TRUE OR UNKNOWN = TRUE`, `FALSE AND UNKNOWN = FALSE`) vs naive boolean `None -> False` collapse |
| 3 | `f3_vuln_patch_regression` | `devops` | SQLi/path-traversal remediator + zero-regression API shim + exploit/caller test suite + advisory/manifest | Fixing SQL injection in `ORDER BY` + `../` path traversal without breaking legitimate callers (`sort_by="price_cents"`, `"guides/quickstart.md"`) + coupled `patch_manifest.json` $\leftrightarrow$ `security_advisory.json` |
| 4 | `f4_simpsons_paradox_audit` | `research` | Stratified Simpson's paradox analyzer + crude pooled summarizer + SHA-256 quote provenance + executive brief | Confounded `severity` (`mild` vs `critical`) reverses crude pooled win rate (`Protocol_B` 69% > `Protocol_A` 60%) vs both strata (`Protocol_A` wins 90% vs 80% in mild, 50% vs 35% in critical) |
| 5 | `f5_double_entry_watermark` | `data` | Event-time watermark reorderer (`MAX_LATENESS=300`) + integer-cent zero-sum ledger + dead-letter queue + reconciliation audit | Out-of-order event timestamps (`tx_002` enables `tx_003` only under event-time sorting; `tx_004` dropped as `LATE_WATERMARK`), duplicate `tx_id` idempotency, and coupled `balances.json` $\leftrightarrow$ `audit_summary.json` |
| 6 | `f6_epistemic_narrative_canon` | `writing` | Close-POV epistemic isolator (`t <= 20`) + sensory anti-slop craft + omniscient foreshadowing lore + continuity ledger | Writing `scene_t20.md` from Mira's POV at `t = 20` without leaking `t = 45` `ORION-9` / `reactor_sabotage` secrets promoted by omniscient foreshadowing skill + coupled canon state |
| 7 | `f7_conormal_polysemy_guard` | `devops` | Kubernetes rollout planner + Prometheus SLO gate + Helm rollback + YAML manifest validator | Adversarial polysemic prompt (*Regency romance fanfiction about Plaid interns building Storybook cards*): tests conormal domain guard (`ABSTAIN_OFF_MANIFOLD`) vs helpful off-manifold compliance |

## Running Locally with `agy` + Sonnet 5.5

From the repository root on a machine with `agy` installed on `PATH`:

```bash
python3 evals/manifold_7family/run_agy_sonnet_bench.py run \
  --agy-bin agy \
  --judge-model claude-sonnet-5-5 \
  --work-dir /tmp/sc_7fam_agy \
  --out-json evals/manifold_7family/results/agy_sonnet55_report.json \
  --out-md evals/manifold_7family/RESULTS_AGY_SONNET55.md
```

If your local `agy` wrapper uses custom CLI flags, pass `--cmd-template` (placeholders: `{agy}`, `{model}`, `{model_flag}`, `{prompt_file}`, `{cwd}`):

```bash
python3 evals/manifold_7family/run_agy_sonnet_bench.py run \
  --cmd-template '{agy} {model_flag} --prompt-file "{prompt_file}"' \
  --judge-model claude-sonnet-5-5
```

## Stepped Execution (`build_benchmark.py` / `prepare-judge` / `finalize`)

```bash
# 1. Materialize the 7-family suite and 21 clean isolated workspaces
python3 evals/manifold_7family/build_benchmark.py \
  --suite-dir /tmp/sc_7fam_live/suite \
  --prepare-runs /tmp/sc_7fam_live/runs

# 2. After running 1 solver call per workspace, run exogenous oracles & build blind shuffled judge packets
python3 evals/manifold_7family/run_agy_sonnet_bench.py prepare-judge \
  --suite-dir /tmp/sc_7fam_live/suite \
  --runs-dir /tmp/sc_7fam_live/runs \
  --packets-dir /tmp/sc_7fam_live/judge_packets

# 3. De-anonymize blind judge JSON verdicts into aggregate JSON + Markdown scorecards
python3 evals/manifold_7family/run_agy_sonnet_bench.py finalize \
  --packets-dir /tmp/sc_7fam_live/judge_packets \
  --verdicts-dir /tmp/sc_7fam_live/verdicts \
  --out-json evals/manifold_7family/results/vm_live_report.json \
  --out-md evals/manifold_7family/RESULTS.md
```

See [`RESULTS.md`](./RESULTS.md) and [`results/vm_live_report.json`](./results/vm_live_report.json) for full benchmark telemetry and blind-judge rationales.
