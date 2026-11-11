---
name: skillcompose
description: >-
  Principled Kleisli, information-theoretic, and control-theoretic skill composition & upgrade
  meta-skill via /skillcompose [query|--pin owner/repo@skill]
  [--domain writing|devops|data|research|automation] [--n N]
  [--discover-only|--resume|--status|--local-only|--remix-plan-only]. Replaces naive "best-of-GitHub"
  concatenation with monotone submodular + JSD/NCD Kolmogorov skill selection (with Nemhauser-Wolsey
  optimality certificate), typed Kleisli transducer wiring (sequential sufficient-statistic adapters,
  separation-logic parallel tensors, pullback invariant joins, guarded ABSTAIN coproducts), Parnas
  progressive-disclosure compilation (compose_skills.py), read-only post-dominator verification gates
  (verify_dominator_gate.py), and 50 MDL/Lyapunov-ratcheted forge rounds. Use when the user invokes
  /skillcompose or $skillcompose, or asks for principled/algebraic/information-theoretic skill
  composition or remixing.
---

# `/skillcompose`

**Principled Marketplace Skill Composition: Submodular JSD+NCD Selection (Nemhauser–Wolsey Certified) → Kleisli Transducer & Separation-Logic Wiring (`compose_skills.py` / `wiring_compiler.py`) → Parnas Module Encapsulation + Auto-Generated Read-Only Post-Dominator Gate (`verify_dominator_gate.py`) → 50 MDL & Lyapunov-Ratcheted Forge Rounds → Multi-Host Install.**

Baseline predecessor: `/skillremix` (heuristic diversity + prose plan). Prefer **`/skillcompose`** whenever combining $N \ge 2$ skills or requiring mathematical coverage, type-safe Kleisli handoffs, and exogenous anti-DPI verification.

Proof / offline gates: [PROOF.md](PROOF.md).  
Formal foundations (Information Theory, Software Engineering Kleisli Composition, Agentic Control): [references/theory.md](references/theory.md).

## Why `/skillcompose` Strictly Dominates a "Compilation of the Best of GitHub"

1. **Submodular + Kolmogorov/NCD Selection (`submodular_select.py`) vs Popularity Top-N:** Ranking by stars/installs collapses onto redundant entry-stage generators ($I(s_i; s_j) \gg 0$) while leaving specification, static contracts, execution observation, and adversarial verification uncovered—and naive name-Jaccard admits polysemic traps (`plaid`, `storybook`). `submodular_select.py` maximizes monotone noisy-OR stage coverage minus blended Jensen-Shannon + Normalized Compression Distance ($d_{\text{NCD}}$) redundancy and off-domain divergence, emitting an instance-specific **Nemhauser–Wolsey optimality ratio certificate**.
2. **Mechanical Kleisli & Separation-Logic Compilation (`compose_skills.py`, `wiring_compiler.py`):** Models each skill as an open effectful Kleisli transducer $\mathcal{S} = \langle I, O, P, Q, \mathcal{F}, \mathcal{E}, \mathcal{B}\rangle$ and compiles them via five operators: **Sequential Pipe with Sufficient-Statistic Adapter** ($S_2 \circ_\alpha S_1$, $Q_1 \implies P_2$), **Parallel Tensor** under Concurrent Separation Logic ($\mathcal{W}_1 \cap (\mathcal{W}_2 \cup \mathcal{R}_2) = \emptyset$), **Pullback Join** ($\pi_K(O_1) = \pi_K(O_2)$), **Guarded Coproduct** (`ABSTAIN`), and **Orthogonal Feedback Loop** ($\mathcal{W}(S_{\text{gate}}) = \emptyset$).
3. **Breaking the Data Processing Inequality (DPI):** Pure-prompt chains ($X \to M_1 \to \dots \to M_k$) monotonically lose ground-truth mutual information ($I(Y^*; M_k) \le I(Y^*; M_1)$). `compose_skills.py` injects exogenous script channels and auto-generates `scripts/verify_dominator_gate.py`, which SHA-256-snapshots deliverables before running exogenous checks and fails with exit `2` if any critic mutates a protected target.
4. **Parnas Information Hiding & MDL Anti-Padding (`information_gain.py`):** Encapsulates member bodies in `references/members/<slug>.md` so root `SKILL.md` stays $O(N)$ lines (high Attention Channel SNR), and gates every forge round on conditional Lempel–Ziv novelty (`info_density >= 0.10`) and Lyapunov debt descent ($\Delta \Phi \le 0$).

## Fast One-Command Mechanical Composition (`compose_skills.py`)

When candidate skills are already discovered/materialized, compile a complete Parnas-encapsulated Kleisli skill package directly:

```bash
python3 "${HOME}/.gemini/config/skills/skillcompose/scripts/compose_skills.py" \
  --candidates "$WIP/discovery/candidates.jsonl" \
  --n "$N" --domain "$DOMAIN" --query "$QUERY" \
  --out-dir "$DEST_SKILL_DIR" --skill-name "$SKILL_NAME"
```

## When NOT to use

- Greenfield-only invention with **no** marketplace members → use `/randomskill` (or write a skill from scratch), not `/skillcompose`.
- You only need a one-line tip or typo fix in an existing skill (no discover/compose/forge/ship loop).
- The goal is to **bypass** license/adoption gates to republish proprietary or GPL skills.
- You intend to claim forge "done" from chat narration without `ship_check.py` / `verify_dominator_gate.py` PASS.
- Offline / no-network runs that still require live `skills find` without `--local-only` / cache / `--pin`.

## Non-triggers (do not fire)

- User asks to "improve writing" or "debug CI" without asking to compose/upgrade/remix **skills**.
- User pastes a private skill path and only wants edits in-place with no composition or forge rounds.
- User requests `--status` / `--resume` alone — answer the status pack; do not start a new discover.



```bash
CALLER_CWD="$(pwd)"
ARGS="${ARGUMENTS:-}"
SCRIPTS="${HOME}/.gemini/config/skills/skillcompose/scripts"   # Antigravity global skill scripts/
ROUNDS=50
```

Parse flags first:

```bash
python3 "$SCRIPTS/parse_args.py" $ARGS > /tmp/sr_args.json
# mode: upgrade (default) | remix (--n N, N>=2)
```

Modes: default single-upgrade · **`--n N` remix** · `--discover-only` · `--audit-only` · `--remix-plan-only` · `--resume --wip PATH` · `--status --wip PATH` · `--local-only` · `--ask-phases` / `--ask-themes` · `--private` · `--domain <pack>`.

Refusal / FAIL exits are **2** across parse_args, license_gate, propose_remix, forge_log, check_phases, unify_wholeness, and ship_check (PASS = 0).


## COMPARISON.md / neighbors (P1–P2)

After fork/init, keep `COMPARISON.md` (single-upgrade) or `REMIX_PLAN.md` + `WHOLENESS.md` (remix)
honest about **neighbors**: name 2–3 marketplace alternatives, what this fork/package does that
they do not, and what it still does worse. `audit_incumbent` flags `shallow-vs-neighbors` when
this is missing — address it before claiming enhance/metrics phases done.

## Operator UX

Prefer `resume_forge.py status --wip … --json` (compact by default) over re-running discover.
On refusal JSON, trust `error` + exit **2**, not a piped `tee|head` status.

## Forge phases (replaces T1–T5)

| Rounds | Kind | Job |
|---|---|---|
| **1–10** | `unify` | Unified whole **strictly more than the sum of its parts** |
| **11–20** | `enhance` | Focused, enhanced abilities |
| **21–44** | `metrics` | Undeniable, reproducible, non-falsified best-in-some-way metrics; reflect + **fix** when not best |
| **45–50** | `awesome` | Actually build something awesome (e.g. a novel) **or** find a ≥99%-confident real bug in someone else's public repo that needed this tool |

Details: `references/forge_phases.md`.

## Adoption floor (no popularity ceiling)

| Signal | Keep | Reject |
|---|---|---|
| skills.sh installs | **≥ 80** (no default ceiling; highly popular OK) | `<80` |
| GitHub stars | **≥ 15** (no default ceiling) | `<15` unless installs meet floor |
| License | MIT/Apache/BSD/ISC/0BSD/Unlicense/CC0/MPL | GPL/AGPL/proprietary unknown without `--allow-unknown` |
| Shape | has `SKILL.md` | husk / no skill file |

Optional per-run caps: `--max-installs` / `--max-stars`. Details: `references/middling_band.md`.

---

## Phase 0 — Setup

```bash
python3 "$SCRIPTS/parse_args.py" $ARGS > /tmp/sr_args.json || exit 2
# parse_args runs args_preflight: --status/--resume REQUIRE a real
# skillremix-wip-* (or randomupgrade-wip-*) --wip; empty/cwd rejected (exit 2).

# False-done guard (transfer): refuse forge/clone when early-stop flags set
python3 "$SCRIPTS/mode_guards.py" --args-json /tmp/sr_args.json --action forge --json || true
# parse_args already rejects contradictory --status/--resume and early-stop∧--resume

STATUS="$(python3 -c 'import json; print(json.load(open("/tmp/sr_args.json"))["status"])')"
RESUME="$(python3 -c 'import json; print(json.load(open("/tmp/sr_args.json"))["resume"])')"
WIP_ARG="$(python3 -c 'import json; print(json.load(open("/tmp/sr_args.json")).get("wip") or "")')"
DISCOVER_ONLY="$(python3 -c 'import json; print(json.load(open("/tmp/sr_args.json"))["discover_only"])')"
AUDIT_ONLY="$(python3 -c 'import json; print(json.load(open("/tmp/sr_args.json"))["audit_only"])')"
REMIX_PLAN_ONLY="$(python3 -c 'import json; print(json.load(open("/tmp/sr_args.json"))["remix_plan_only"])')"

if [[ "$STATUS" == "True" ]]; then
  python3 "$SCRIPTS/resume_forge.py" status --wip "$WIP_ARG" --json
  exit 0
fi

if [[ "$RESUME" == "True" ]]; then
  WIP_DIR="$WIP_ARG"
else
  RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)"
  WIP_DIR="$CALLER_CWD/skillremix-wip-$RUN_ID"
  mkdir -p "$WIP_DIR"/{discovery,forge,upstream}
fi
```

Tell the user: *Working in `$WIP_DIR`.*

On `--status`: status JSON includes compact `chosen_ids`, `progress`, `resume_hint`,
`resume_ready` (pass `--full` for complete chosen_n member blobs) — then stop.  
On `--resume`: load status, follow `resume_hint`, continue Phase 4 from `next_round`.

---

## Branch: remix vs single upgrade

```bash
MODE="$(python3 -c 'import json; print(json.load(open("/tmp/sr_args.json"))["mode"])')"
N="$(python3 -c 'import json; print(json.load(open("/tmp/sr_args.json")).get("n") or "")')"
```

- If `MODE=remix` → follow **Remix path** (below), then shared Phase 4–6 with round map from `remix_plan.json`.
- Else → **Single-upgrade path** (Phases 1–3 classic).

---

## Remix path (`--n N`)

Full protocol: `references/remix_mode.md`.

### R1 — Discover pool (domain-exact + practice-support when N is large)

When `--n` is **large** (≥5 by default), discovery must **not** only search skills labeled for `--domain`. Also pull **practice-support** skills — things you would need while practicing the domain end-to-end (verify, evals, continuity, git, research notes, …) even if those skills are also used elsewhere.

```bash
python3 "$SCRIPTS/discover_skills.py" \
  --out "$WIP_DIR/discovery/candidates.jsonl" \
  --domain "${DOMAIN:-general}" \
  --extra "$QUERY" \
  --n "$N" \
  --practice-support auto \
  --json

python3 "$SCRIPTS/enrich_github.py" \
  --candidates "$WIP_DIR/discovery/candidates.jsonl" \
  --out "$WIP_DIR/discovery/candidates_enriched.jsonl" --json
```

### R2 — Submodular mutual-information pick (coverage − JSD redundancy − off-domain divergence)

```bash
python3 "$SCRIPTS/pick_n_eligible.py" \
  --candidates "$WIP_DIR/discovery/candidates_enriched.jsonl" \
  --n "$N" \
  --domain "${DOMAIN:-}" \
  --query "$QUERY" \
  --strategy submodular \
  --seed "${SEED:-$RUN_ID}" \
  --practice-mix auto \
  --write-chosen "$WIP_DIR/discovery/chosen_n.json" --json \
  | tee "$WIP_DIR/discovery/pick_n.json"
# Emits information_telemetry + vs_github_popularity_top_n lift directly in chosen_n.json.

# Coherence gate (UC-driven): reject off-domain members before clone/propose
python3 "$SCRIPTS/remix_coherence_gate.py" \
  --chosen-n "$WIP_DIR/discovery/chosen_n.json" \
  --query "$QUERY" --domain "${DOMAIN:-}" --json \
  | tee "$WIP_DIR/discovery/coherence.json"
# On FAIL: exclude weak ids, re-pick, or stop — do not propose_remix yet.
```

License-gate **each** chosen id (retry/exclude failures up to 2N attempts while filling N).

Tell user: *Remixing N skills: \<ids\> → `$WIP_DIR`.*

### R3 — Clone + audit each; decide buffs

For each member in `chosen_n.json`:

```bash
# clone into $WIP_DIR/upstream/<safe_id>/
python3 "$SCRIPTS/locate_skill.py" --repo "$REPO" --skill-name "<name>" --json --quiet
python3 "$SCRIPTS/audit_incumbent.py" \
  --skill-dir "$SKILL_SRC" \
  --out "$WIP_DIR/discovery/audits/<safe_id>.json" --json
```

### R4 — Compile algebraic wiring graph + propose subskills/superskill/buff map

```bash
python3 "$SCRIPTS/propose_remix.py" \
  --chosen-n "$WIP_DIR/discovery/chosen_n.json" \
  --audits "$WIP_DIR/discovery/audits" \
  --out "$WIP_DIR/forge/remix_plan.json" \
  --domain "$DOMAIN" \
  --name "${NAME:-}" \
  --forge-rounds "$ROUNDS" --json
# Also emits $WIP_DIR/forge/wiring_graph.json + WIRING_CONTRACT.md and runs static verification
# (type_safety, separation_logic, dpi_exogenous_grounding, dominator_orthogonality).
python3 "$SCRIPTS/wiring_compiler.py" verify --graph "$WIP_DIR/forge/wiring_graph.json" --json
```

**Agent refinement (required):** read member SKILL.md files + marketplace neighbors; rewrite subskills/superskill so the end-to-end job is real (not a name mashup). Keep exactly the buff decisions honest: heavy buff where composition would false-done.

Write `REMIX_PLAN.md` into the package root (from refined JSON).

`--discover-only` / `--remix-plan-only` → print plan + stop.

### R5 — Init package + forge per round_map

```bash
PKG_NAME="${NAME:-$(python3 -c 'import json; print(json.load(open("'"$WIP_DIR"'/forge/remix_plan.json"))["superskill"]["name"])')}"
PKG_DIR="$WIP_DIR/$PKG_NAME"
mkdir -p "$PKG_DIR"/{skills,subskills,scripts,references,evals,forge}
# Buff each member into $PKG_DIR/skills/<slug>-upgraded via init_fork + forge rounds from round_map
# Author each subskill under $PKG_DIR/subskills/<name>/
# Author superskill as $PKG_DIR/SKILL.md (orchestrator)
```

Then shared Phase 4 using fixed phases (unify → enhance → metrics → awesome). Still ≥3 surfaces/round, **≥1000 chars/round**, **one commit/round**. After round 50, `ship_check` (+ `unify_wholeness` for remix) must PASS.

Ship the **package** (superskill + subskills + buffed members), dual-install **superskill name** (and install subskills if they are standalone invocable).

---

## Single-upgrade path — Phase 1 — Discover + enrich + pick

```bash
python3 "$SCRIPTS/discover_skills.py" \
  --out "$WIP_DIR/discovery/candidates.jsonl" \
  --domain "${DOMAIN:-general}" \
  --extra "$QUERY" --json
# Auto-stores into ~/.cache/skillremix/discover (opt out: --no-cache-store).
# Offline: add --local-only to reuse cache only (exit 2 on miss; no skills find).
# Optional pre-check: python3 "$SCRIPTS/discover_cache.py" --domain … --extra … --lookup
# After discover: python3 "$SCRIPTS/discover_cache.py" --domain … --extra … --store …  # redundant if auto-store on

python3 "$SCRIPTS/enrich_github.py" \
  --candidates "$WIP_DIR/discovery/candidates.jsonl" \
  --out "$WIP_DIR/discovery/candidates_enriched.jsonl" --json

python3 "$SCRIPTS/pick_eligible.py" \
  --candidates "$WIP_DIR/discovery/candidates_enriched.jsonl" \
  ${PIN:+--pin "$PIN"} \
  --min-installs … ${MAX_INSTALLS:+--max-installs "$MAX_INSTALLS"} --seed "${SEED:-$RUN_ID}" \
  --write-chosen "$WIP_DIR/discovery/chosen.json" --json \
  | tee "$WIP_DIR/discovery/pick.json"

# Pin fastpath: if --pin and you want to skip discover, you may instead:
#   : > "$WIP_DIR/discovery/candidates_enriched.jsonl"
#   python3 "$SCRIPTS/pick_eligible.py" --candidates … --pin "$PIN" --write-chosen …
# (pick_eligible calls pin_fastpath.py when the pin is absent from candidates)

python3 "$SCRIPTS/license_gate.py" --chosen "$WIP_DIR/discovery/chosen.json" --json
```

FAIL license → pick next eligible candidate (exclude id), retry up to 5 times.

Also search GitHub when skills.sh is thin (`gh search repos` / `gh search code`); append to candidates.jsonl.

`--discover-only` → print chosen + stop.

Tell user: *Upgrading: \<id\> (installs≈N) → `$WIP_DIR`.*

---

## Phase 2 — Clone + locate + init fork

```bash
git clone --depth 50 "$URL" "$WIP_DIR/upstream/repo"

python3 "$SCRIPTS/locate_skill.py" \
  --repo "$WIP_DIR/upstream/repo" \
  --skill-name "<name-from-id>" \
  --subdir "<from chosen>" --json --quiet
# → SKILL_SRC

FORK_NAME="${NAME:-<skill>-upgraded}"
python3 "$SCRIPTS/init_fork.py" \
  --src "$SKILL_SRC" \
  --dest "$WIP_DIR/$FORK_NAME" \
  --fork-name "$FORK_NAME" \
  --chosen "$WIP_DIR/discovery/chosen.json" \
  --dual-installer "$SCRIPTS/install_skill_dual.sh" --json

FORK_DIR="$WIP_DIR/$FORK_NAME"
git -C "$FORK_DIR" init -b main
git -C "$FORK_DIR" add -A
git -C "$FORK_DIR" commit -m "fork: baseline from $INCUMBENT_ID before upgrade forge"
```

---

## Phase 3 — Audit → lock forge phases (not T1–T5)

```bash
python3 "$SCRIPTS/audit_incumbent.py" \
  --skill-dir "$SKILL_SRC" \
  --out "$WIP_DIR/discovery/audit.json" \
  --phases-out "$WIP_DIR/forge/forge_phases.json" --json

python3 "$SCRIPTS/write_upgrade_plan.py" \
  --phases "$WIP_DIR/forge/forge_phases.json" \
  --out "$FORK_DIR/UPGRADE_PLAN.md" \
  --incumbent "$INCUMBENT_ID"

git -C "$FORK_DIR" add -A
git -C "$FORK_DIR" commit -m "plan: lock 50-round forge phases (unify/enhance/metrics/awesome)"
```

List the four phases to the user. If `--ask-phases` / `--ask-themes`, pause. Else continue.  
`--audit-only` → stop after audit/plan.

Fixed map: **1–10 unify · 11–20 enhance · 21–44 metrics · 45–50 awesome**. Each round = own prompt @ **90s** spacing.

---

## Phase 4 — Fifty **real** rounds (one prompt each, 90s apart)

```bash
: > "$WIP_DIR/forge/usefulness_forge.jsonl"
printf '# Upgrade forge\n\n' > "$FORK_DIR/USEFULNESS_FORGE.md"
export WIP_DIR FORK_DIR
MIN_CHARS=1000
```

*Starting upgrade forge: $ROUNDS rounds — each round = one commit + ≥$MIN_CHARS product chars; kind from phase.*

**Per-round procedure** (do not summarize away; do not batch):

```bash
NEXT="$(python3 "$SCRIPTS/resume_forge.py" next --wip "$WIP_DIR" --rounds "$ROUNDS" --json)"
R="$(python3 -c 'import json,sys; print(json.load(sys.stdin)["next_round"] or "")' <<<"$NEXT")"
[[ -n "$R" ]] || { python3 "$SCRIPTS/ship_check.py" --fork "$FORK_DIR" --rounds "$ROUNDS" --min-chars 1000 --json; exit 0; }
KIND="$(python3 -c 'import json,sys; print(json.load(sys.stdin).get("kind") or "")' <<<"$NEXT")"
THEME="$(python3 -c 'import json,sys; print(json.load(sys.stdin).get("theme") or "")' <<<"$NEXT")"
# 0) Mark busy so an overlapping timer wake will NOT double-start:
python3 "$SCRIPTS/agent_busy.py" acquire --wip "$WIP_DIR" --round "$R" --json
# 1) Answer usefulness question into USEFULNESS_FORGE.md (this phase only)
# 2) Implement multi-surface leap for THIS round only (≥1000 chars)
# 3) Commit + log (forge_round.sh also releases agent_busy.lock):
git -C "$FORK_DIR" add -A
git -C "$FORK_DIR" commit -m "forge(${R}/${ROUNDS}): ${THEME} — ${GAP}"
bash "$SCRIPTS/forge_round.sh" "$R" "$ROUNDS" "$THEME" "$GAP" "$ADDITION" \
  '["procedure","code","docs"]' '["SKILL.md"]' "[\"$INCUMBENT_ID\"]" "$KIND"
# 4) Build the standalone prompt for round R+1:
if [[ "$R" -lt "$ROUNDS" ]]; then
  python3 "$SCRIPTS/forge_phases.py" --prompt-round $((R+1)) --wip "$WIP_DIR" --fork "$FORK_DIR" --json
fi
```

4. **Arm NEXT round wake in 90s — then STOP forging this turn:**
   - **In Antigravity (mandatory):** call the native **`schedule` tool** with `DurationSeconds: 90` (or `round_interval_sec` from `/tmp/sr_args.json`) and `Prompt` set to the `prompt` text from `forge_phases.py --prompt-round $((R+1))`. Then **end your turn immediately** (call no more tools) and wait for the wakeup notification. **Never** use a shell `sleep` command as a timer in Antigravity.
   - *(Legacy Cursor/CLI fallback only when `schedule` tool is absent: `schedule_forge_loop.sh --from $((R+1)) --to $((R+1)) --interval 90`.)*

**On `schedule` timer wakeup:** first run `python3 "$SCRIPTS/agent_busy.py" check --wip "$WIP_DIR" --json`. If busy (exit `0`), re-arm `schedule` with `DurationSeconds: 15` and the same `Prompt`, then stop. Otherwise run `resume_forge.py next` (so an already-logged round is skipped cleanly), execute **exactly that one round**, and re-arm `schedule` for `R+1` (`DurationSeconds: 90`).

Validate (must PASS — else keep looping):

```bash
python3 "$SCRIPTS/forge_log.py" validate --log "$WIP_DIR/forge/usefulness_forge.jsonl" \
  --rounds "$ROUNDS" --min-chars 1000 --strict-phases --json
python3 "$SCRIPTS/check_phases.py" --phases "$WIP_DIR/forge/forge_phases.json" \
  --log "$WIP_DIR/forge/usefulness_forge.jsonl" --rounds "$ROUNDS" --json
# remix — strict sum-of-parts (blocking):
python3 "$SCRIPTS/unify_wholeness.py" --package "$FORK_DIR" --rounds "$ROUNDS" --min-chars 1000 --json
```

Update `COMPARISON.md` / `REMIX_PLAN.md` / `WHOLENESS.md` / `METRICS.md` / `AWESOME_PROOF.md` as phases complete. Protocol: `references/round_protocol.md`, `references/forge_phases.md`, `references/wholeness.md`.

**Done is not “we talked about 50 rounds.”** Done is `ship_check.py` PASS. Never batch rounds in one turn.
---

## Phase 5 — Ship-check + publish

```bash
cp "$WIP_DIR/forge/usefulness_forge.jsonl" "$FORK_DIR/forge/"
bash "$SCRIPTS/dry_run_gates.sh"   # FULL run only — do NOT use --fast for publish
# expect review/last_dry_run.json {"mode":"full",...}; ship_check FAILs if mode=fast
# --fast refuses to clobber mode=full unless --force-fast
python3 "$SCRIPTS/ship_check.py" --fork "$FORK_DIR" --rounds "$ROUNDS" --min-chars 1000 --json
```

FAIL → fix (P1 wholeness / P3 metrics / P4 awesome proof); **do not publish** until PASS. Requires `METRICS.md` + `AWESOME_PROOF.md`. Remix also requires `unify_wholeness` PASS.
```bash
gh repo create "${GH_OWNER}/${FORK_NAME}" --public --source="$FORK_DIR" --remote=origin --push
```

Optional: `mv "$FORK_DIR" "$CALLER_CWD/$FORK_NAME"`.

---

## Phase 6 — Multi-host install (mandatory)

```bash
bash "$SCRIPTS/install_skill_dual.sh" "$FORK_DIR" --name "$FORK_NAME"
```

Verify `~/.gemini/config/skills/$FORK_NAME/SKILL.md`, `~/.claude/skills/$FORK_NAME/SKILL.md`, `~/.cursor/skills/$FORK_NAME/SKILL.md`, and `~/.codex/skills/$FORK_NAME/SKILL.md`.

*Installed globally: `/$FORK_NAME` → ~/.gemini/config/skills + ~/.claude/skills + ~/.cursor/skills + ~/.codex/skills. Repo: \<url\>.*

Refresh this meta-skill after editing it:

```bash
bash "$SCRIPTS/install_skill_dual.sh" "$CALLER_CWD/skillremix" --name skillremix
# keep legacy alias installed:
bash "$SCRIPTS/install_skill_dual.sh" "$CALLER_CWD/randomupgrade" --name randomupgrade
```

---

## Script index

| Script | Job |
|---|---|
| `parse_args.py` | Flags → JSON (`mode`, `--n`, …) |
| `discover_skills.py` | Multi-query `skills find` → candidates.jsonl |
| `enrich_github.py` | stars / license / pushedAt |
| `pick_eligible.py` | Adoption-floor filter + seeded pick (single; no default max; popular OK). Alias: `pick_middling.py` |
| `pick_n_eligible.py` | Diverse / submodular pick of N eligible skills (remix; popular OK). Alias: `pick_n_middling.py` |
| `submodular_select.py` | Information-theoretic submodular coverage − JSD redundancy − off-domain divergence selector |
| `wiring_compiler.py` | Kleisli port typechecker, separation-logic parallel checker, pullback & dominator verifier |
| `information_gain.py` | Conditional Lempel-Ziv MDL novelty, Context-SNR, and Lyapunov debt $\Phi$ telemetry |
| `propose_remix.py` | Buff map + algebraic wiring graph + subskills + superskill scaffold |
| `license_gate.py` | Forkable license check |
| `locate_skill.py` | Monorepo SKILL.md locator |
| `init_fork.py` | Scaffold fork (UPSTREAM/COMPARISON/install/README) |
| `audit_incumbent.py` | Gap audit + lock 4 forge phases |
| `write_upgrade_plan.py` | UPGRADE_PLAN.md from forge_phases.json |
| `forge_phases.py` | Canonical 1–10/11–20/21–44/45–50 phase model + per-round prompts |
| `schedule_forge_loop.sh` | Legacy Cursor/CLI 90s wake helper (in Antigravity, use native `schedule` tool instead) |
| `agent_busy.py` | acquire/release/check mid-round lock so timer wakes do not double-start a round |
| `forge_log.py` / `forge_round.sh` | Round log append; refuses <1000 chars; enforces phase kinds |
| `measure_chars.py` | Product-char churn for HEAD commit |
| `unify_wholeness.py` | Strict sum-of-parts / unification gate |
| `check_phases.py` | All 4 phases correctly tagged in log |
| `resume_forge.py` | status / next round (+ kind, resume_hint, mode, chosen_ids) |
| `args_preflight.py` | Validate --status/--resume WIP (never cwd false-status) |
| `pin_fastpath.py` | Resolve `--pin` via gh without full discover |
| `remix_coherence_gate.py` | Reject off-domain remix members before propose |
| `ship_check.py` | Pre-publish gate (forge mass + METRICS + AWESOME + wholeness) |
| `install_skill_dual.sh` | Antigravity (`~/.gemini/config/skills`) + Claude + Cursor + Codex install |


## Non-negotiables

- Adoption floor (no popularity ceiling) + license gate
- **No T1–T5 ladder** — fixed phases: unify → enhance → metrics → awesome
- **50 real commits × ≥1000 chars**, one scheduled turn per round spaced **90s** via `schedule` (never shell `sleep`), phase-correct `kind`
- Remix: `unify_wholeness` PASS after P1; ship needs `METRICS.md` + `AWESOME_PROOF.md`
- Resumable; ship_check PASS before publish — nominal round claims do not count
- Cite upstream; multi-host install (`~/.gemini/config/skills` + Claude + Cursor + Codex) before done
- Default to active Antigravity model (`inherit` for subagents unless user requests otherwise); never invent install counts

## References

- `references/middling_band.md`
- `references/forge_phases.md` — **canonical phase plan (replaces T1–T5)**
- `references/upgrade_themes.md` — legacy redirect note
- `references/round_protocol.md`
- `references/wholeness.md` — strict sum-of-parts definition + predicates
- `references/remix_mode.md` — `--n` end-to-end remix
- `references/pipeline.md` — end-to-end command cheat sheet

## Helpers
When importing `forge_phases` / other scripts as modules: `PYTHONPATH="$SCRIPTS" python3 -c 'from forge_phases import PHASES'`.


```bash
# Adversarial args / empty-WIP refusal metric
python3 metrics/adversarial-args/measure.py && python3 metrics/adversarial-args/plot.py
```

Preflight WIP checks: `scripts/args_preflight.py` (also invoked from `parse_args.py`).

```bash
python3 metrics/remix-coherence/measure.py && python3 metrics/remix-coherence/plot.py
```

```bash
python3 metrics/status-pack-bytes/measure.py && python3 metrics/status-pack-bytes/plot.py
```

```bash
python3 metrics/propose-audits-gate/measure.py && python3 metrics/propose-audits-gate/plot.py
```
