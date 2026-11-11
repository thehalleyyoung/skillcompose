# `skillcompose` (`/skillcompose`)

**Principled Information-Theoretic, Software-Engineering (Kleisli + Separation Logic + Parnas), and Control-Theoretic Meta-Skill for Agent Skill Composition.**

`skillcompose` upgrades and composes marketplace agent skills into provably wired, high-SNR transducer pipelines—replacing naive *"compilations of the best of GitHub"* (top-stars concatenation + prompt routers) with formal submodular selection, typed Kleisli composition, Parnas progressive disclosure, exogenous DPI-breaking observation, and orthogonal read-only post-dominator verification gates.

Full formal monograph: [`references/theory.md`](references/theory.md) · Offline verification card: [`PROOF.md`](PROOF.md).

---

## Why "Compiling the Best of GitHub" Fails — and What `skillcompose` Does Instead

| Failure Mode of Naive "Best-of-GitHub" Compilation | Formal Principle in `skillcompose` | Executable Implementation |
|---|---|---|
| **1. Popularity Redundancy Collapse & Polysemy Traps:** Sorting by stars/installs picks $N$ near-duplicate entry-stage generators ($I(S_i; S_j) \gg 0$) while leaving contracts, execution, rollback, and verification uncovered—or admits polysemic traps (`plaid`, `storybook`). | **Monotone Submodular Noisy-OR Coverage** across 6 Kleisli roles minus blended **Jensen–Shannon ($\text{JSD}$) + Cilibrasi–Vitányi Normalized Compression Distance ($d_{\text{NCD}}$)** similarity and off-domain divergence, with an online **Nemhauser–Wolsey optimality bound certificate**. | [`scripts/submodular_select.py`](scripts/submodular_select.py) |
| **2. Untyped Prompt Concatenation (Zero PID Synergy):** Dumping 4 `SKILL.md` files into one prompt lacks interface contracts; ambiguities propagate silently downstream. | **Open Effectful Kleisli Transducers** $\mathcal{S} = \langle I, O, P, Q, \mathcal{F}, \mathcal{E}, \mathcal{B}\rangle$ composed via **Sequential Sufficient-Statistic Adapters** ($S_2 \circ_\alpha S_1$, $Q_1 \implies P_2$), **Concurrent Separation Logic Tensors** ($\mathcal{W}_1 \cap (\mathcal{W}_2 \cup \mathcal{R}_2) = \emptyset$), **Pullback Joins** ($\pi_K(O_1)=\pi_K(O_2)$), and **Guarded `ABSTAIN` Coproducts**. | [`scripts/wiring_compiler.py`](scripts/wiring_compiler.py), [`scripts/compose_skills.py`](scripts/compose_skills.py) |
| **3. Data Processing Inequality (DPI) Decay:** Pure-prompt chains $Y^* \to X \to M_1 \to \dots \to M_k$ satisfy $I(Y^*; M_k) \le I(Y^*; M_1)$—hallucinations cannot be corrected without fresh environment entropy. | **Exogenous Grounding ($\mathcal{I}_{\text{exo}} > 0$):** Every compiled pipeline requires deterministic script/SQL/AST/test observation channels injecting fresh conditional mutual information $I(Y^*; E_t \mid M_t) > 0$. | [`scripts/compose_skills.py`](scripts/compose_skills.py), [`scripts/information_gain.py`](scripts/information_gain.py) |
| **4. Attention Channel SNR Dilution:** Concatenating $N$ verbose skills inflates root `SKILL.md` to $O(\sum |S_i|)$, burying critical invariants. | **Parnas Information Hiding:** Root `SKILL.md` stays compact ($O(N)$ typed stage links) while member details are encapsulated under `references/members/<slug>.md` (`encapsulation_ratio >= 0.20`, typically `> 0.80`). | [`scripts/compose_skills.py`](scripts/compose_skills.py), [`scripts/wiring_compiler.py`](scripts/wiring_compiler.py) |
| **5. Common-Mode Self-Grading & Goodhart Padding:** Letting a mutator grade its own output (or padding forge commits with prose) causes correlated false-`DONE`. | **Post-Dominator Orthogonal Gate ($\mathcal{W}(S_{\text{gate}}) = \emptyset$)** with SHA-256 non-mutation checks (`verify_dominator_gate.py`) + **Conditional DEFLATE/LZ Novelty** (`info_density >= 0.10`) & **Lyapunov Debt Ratchet** ($\Delta \Phi \le 0$). | [`scripts/compose_skills.py`](scripts/compose_skills.py), [`scripts/information_gain.py`](scripts/information_gain.py), [`scripts/forge_round.sh`](scripts/forge_round.sh) |

---

## Empirical Evaluation (5 Task Families · Blinded Single-Call Claude Sonnet 5.5 Judge)

Evaluated across 5 distinct domains (`f1_data` zero-downtime SQLite evolution, `f2_devops` multi-vulnerability webhook/archive/SSRF remediation, `f3_research` Simpson's paradox & survivorship synthesis, `f4_automation` RFC -> Kleene $K_3$ three-valued policy DSL, `f5_writing` epistemically-partitioned dual-POV fiction) with identical worker budgets (`gemini-3.8-flash-low`) and a single blinded folder-wide `agy --model claude-sonnet-5-5-medium` judge call (`208,642` total tokens across all 15 anonymized candidate outputs) plus 50 held-out executable Python checks:

| Method | Mean Sonnet 5.5 Score | Mean Rank (`1`=Best) | `#1` Wins | Minimax Floor (Worst Family) | Held-Out Executable Oracle |
|---|---|---|---|---|---|
| **`skillcompose` ($N=4$)** | **`87.2 / 100`** | **`1.60`** | **`3 / 5`** | **`79.0`** | **`100.0%` (`50/50`)** |
| `top4_github_compilation` ("Best of GitHub") | `82.0 / 100` | `2.00` | `2 / 5` | `69.0` | `100.0%` (`50/50`) |
| `top1_github` (#1 GitHub Skill) | `79.6 / 100` | `2.40` | `0 / 5` | `68.0` | `96.0%` (`48/50`) |

- **Online Nemhauser–Wolsey Optimality Certificates:** `90.2%–99.7%` of the theoretical global submodular coverage upper bound across all 5 families.
- **Empirical Proof Against Unprincipled Concatenation:** In both `f2_devops` (`69` vs `80`) and `f5_writing` (`78` vs `83`), concatenating the top-4 GitHub skills degraded output quality *below* using the single `#1` GitHub skill alone (Attention SNR dilution + polysemy/contract conflict), whereas `skillcompose` ranked `#1` on both (`87` and `88`).

---

## Install (Antigravity / `agy` + Claude Code + Cursor + Codex)

```bash
git clone https://github.com/thehalleyyoung/skillcompose.git
cd skillcompose
bash install.sh
```

Installs `skillcompose` cleanly into:
- `~/.gemini/config/skills/skillcompose` (Antigravity / `agy`)
- `~/.claude/skills/skillcompose` (Claude Code)
- `~/.cursor/skills/skillcompose` (Cursor)
- `~/.codex/skills/skillcompose` (Codex, auto-generating `agents/openai.yaml` when available)

---

## Usage

### Interactive / Agent Invocation (`/skillcompose`)

```text
/skillcompose --n 4 --domain data "sqlite zero downtime schema migration rollback"
/skillcompose --n 4 --domain devops "webhook security audit patch exploit regression"
/skillcompose --n 4 --domain automation --remix-plan-only
/skillcompose --status --wip ./skillremix-wip-20261111T000000Z
```

### Direct Mechanical Kleisli Compilation (`compose_skills.py`)

Given any discovered/eligible candidate pool (`candidates.jsonl`), mechanically select, audit, wire, encapsulate, and emit a verified composite skill package:

```bash
python3 scripts/compose_skills.py \
  --candidates "$WIP/discovery/candidates.jsonl" \
  --n 4 \
  --domain automation \
  --query "rfc formal grammar parser three valued logic policy dsl" \
  --out-dir ./composed-skill \
  --skill-name policy-dsl-pack
```

### Offline Verification & Metric Gates

```bash
bash scripts/dry_run_gates.sh
python3 metrics/principled-lift/measure.py
```

---

## Repository Layout

- [`SKILL.md`](SKILL.md) — Agent entry point & protocol for `/skillcompose`
- [`references/theory.md`](references/theory.md) — Complete mathematical & software-engineering derivation
- [`scripts/submodular_select.py`](scripts/submodular_select.py) — 6-role noisy-OR submodular selector + JSD + Kolmogorov/NCD + Nemhauser–Wolsey certificate
- [`scripts/wiring_compiler.py`](scripts/wiring_compiler.py) — Kleisli operator classifier, wiring synthesizer, and 5-law static theorem verifier
- [`scripts/compose_skills.py`](scripts/compose_skills.py) — End-to-end Parnas package compiler & read-only `verify_dominator_gate.py` generator
- [`scripts/information_gain.py`](scripts/information_gain.py) — Conditional Lempel–Ziv/DEFLATE commit novelty, Attention SNR, and Lyapunov potential $\Phi$
- [`metrics/`](metrics) — 8 reproducible offline verification suites (including [`metrics/principled-lift/measure.py`](metrics/principled-lift/measure.py))

## License

MIT — see [`LICENSE`](LICENSE).
