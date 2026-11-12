# `skillcompose` (`/skillcompose`)

**Lawvere–Amari Generative Skill Manifold, Kleisli Transducer, Information-Theoretic, and Control-Theoretic Meta-Skill for Agent Skill Synthesis & Composition.**

`skillcompose` does strictly more than compile a *"best-of-GitHub concatenation"* ($\bigwedge_i s_i$) or wire a *"union/router of remixed skills"* ($\bigcup_i s_i$). Modeling each skill rigorously as a **Guarded Conditional Markov Kernel over Structured Outputs** ($s : x \mapsto K_{\eta_s, Q_s}(\cdot \mid x)$ supported on admissible fiber $\mathcal{Y}_s(x) \subseteq \mathcal{Y}$), `skillcompose` treats $N$ marketplace skills as landmark observations on a **Conditional Statistical–Logical Manifold** $\mathfrak{G}_{\mathcal{M}}$—synthesizing a single parameterized generative process via **Galois Conormal Closure**, **Plotkin–Reynolds Anti-Unification**, **Amari Conditional Fisher–Rao Geometry**, **Čech Sheaf Gluing**, and **Post-Dominator Orthogonal Verification**.

Research paper (LaTeX + PDF): [`paper/main.pdf`](paper/main.pdf) ([`paper/main.tex`](paper/main.tex)) · 7-family benchmark: [`evals/manifold_7family/RESULTS.md`](evals/manifold_7family/RESULTS.md) · Self-hosted ML paper skill: [`paper/composed_skill/ml-paper-manifold/SKILL.md`](paper/composed_skill/ml-paper-manifold/SKILL.md) · Formal monograph: [`references/theory.md`](references/theory.md) · Verification card: [`PROOF.md`](PROOF.md).

---

## Why Neither "Concatenating GitHub Skills" Nor "Taking Their Union" Works — and What `skillcompose` Synthesizes Instead

| Failure Mode of Concatenation ($\bigwedge_i s_i$) & Union ($\bigcup_i s_i$) | Formal Principle in `skillcompose` | Executable Implementation |
|---|---|---|
| **1. Constraint-Union Collapse ($Q_i \land Q_j \vdash \bot$):** Concatenating skills that specialize different regimes (e.g., streaming JSONL vs transactional SQLite) produces an empty output fiber ($\mathcal{Y}_{\cap}(x) = \emptyset$). | **Galois Conormal Core ($\Phi_{\text{core}}$) + Plotkin–Reynolds Anti-Unification ($\sqcup_{\text{lgg}}$):** Universal invariants cut out $N^*\mathcal{M}=0$, while conflicting clauses lift into typed **Lawvere Chart Variables** $\theta \in \Theta$ with exact landmark recovery ($\sigma_i^*\mathcal{T}_{\mathcal{M}} \equiv Q_i \land \Phi_{\text{core}}$). | [`scripts/manifold_engine.py`](scripts/manifold_engine.py), [`scripts/compose_skills.py`](scripts/compose_skills.py) |
| **2. Union Rank Deficit & Off-Manifold Mixture Curvature:** A router/mixture $\sum_i w_i K_i$ only covers the $N$ sampled fibers ($0$ probability mass on recombinant coordinates $\theta^* \notin \{\theta^{(i)}\}$) and follows curved $m$-geodesics. | **Amari Conditional Fisher–Rao Tangent Basis & $e$-Geodesic Projection ($\sigma^* : \mathcal{X} \to \Theta$):** Projects any task $x$ onto Fisher-orthonormal tangent generators $V$ and synthesizes $K_{\theta^*(x)}(y \mid x)$ (`project_manifold.py`), halting with exit-`2` `ABSTAIN_OFF_MANIFOLD` outside the conormal domain guard. | [`scripts/manifold_engine.py`](scripts/manifold_engine.py), [`scripts/compose_skills.py`](scripts/compose_skills.py) |
| **3. Popularity Redundancy & Subspace Collapse:** Sorting by stars picks $N$ near-duplicate generators that fail to span either pipeline roles or $T\mathcal{M}$. | **Monotone Submodular Noisy-OR + Kiefer–Wolfowitz Log-Det Fisher Volume** ($M_{\text{role}}(S) + \gamma \frac{1}{2}\log\det(I + \alpha \tilde{\Psi}_S^\top \tilde{\Psi}_S)$) minus blended **JSD + Kolmogorov/NCD** similarity, with an online **Nemhauser–Wolsey optimality certificate**. | [`scripts/submodular_select.py`](scripts/submodular_select.py) |
| **4. Multi-View Gluing Inconsistency ($\delta^0 y \neq 0$):** Separate member skills emit locally plausible files that disagree on shared schemas/denominators—or form contradictory triangle transitions ($\delta^1 g \neq \mathrm{id}$). | **Presheaf Gluing & Čech Cohomology Exactness ($\Gamma(\mathcal{U}, \mathcal{F}) = \ker \delta^0$, $\delta^1 = 0$)** + **Concurrent Separation Logic** ($\mathcal{W}_1 \cap (\mathcal{W}_2 \cup \mathcal{R}_2) = \emptyset$). | [`scripts/wiring_compiler.py`](scripts/wiring_compiler.py), [`scripts/compose_skills.py`](scripts/compose_skills.py) |
| **5. DPI Decay, SNR Dilution, & Self-Grading:** Pure-prompt chains lose ground-truth mutual information ($I(Y^*; M_k) \le I(Y^*; X)$), bloat context, and self-certify errors. | **Parnas Information Hiding** (`encapsulation_ratio > 0.80`), **Exogenous Grounding**, **SHA-256 Read-Only Post-Dominator Gate** ($\mathcal{W}(S_{\text{gate}}) = \emptyset$, `verify_dominator_gate.py`), and **DEFLATE/LZ + Lyapunov Ratchets**. | [`scripts/compose_skills.py`](scripts/compose_skills.py), [`scripts/information_gain.py`](scripts/information_gain.py) |

---

## Empirical Evaluations (7-Family Lawvere–Amari Manifold Study + 5-Family Marketplace Study)

1. **7-Family Lawvere–Amari Manifold Benchmark ([`evals/manifold_7family/RESULTS.md`](evals/manifold_7family/RESULTS.md), [`paper/main.pdf`](paper/main.pdf))**: Single isolated solver call per `(task, regime)` across 7 task families (`f1` streaming+transactional ETL, `f2` zero-downtime SQLite evolution, `f3` Kleene $K_3$ policy DSL, `f4` Simpson's paradox + IPW causal study, `f5` multi-vuln webhook patch + quarantine, `f6` epistemically partitioned dual-POV fiction, `f7` off-domain `plaid` polysemy refusal trap) + blind judge (`agy --model claude-sonnet-5-5` runner):
   - **`manifold` ($\mathfrak{G}_{\mathcal{M}}$)**: **`95.3 / 100`** blind judge · **`100.0%` (`7/7`)** exogenous Python oracle · **`7 / 7`** `#1` wins
   - **`union` ($\bigcup_i s_i$)**: `55.6 / 100` blind judge · `21.4%` exogenous oracle · `0 / 7` `#1` wins
   - **`concat` ($\bigwedge_i s_i$)**: `36.3 / 100` blind judge · `14.3%` exogenous oracle · `0 / 7` `#1` wins
2. **5-Family Marketplace Baseline Benchmark (Blinded Single-Call Claude Sonnet 5.5 Judge + 50 Held-Out Checks)**:
   - **`skillcompose` ($N=4$)**: **`87.2 / 100`** (mean rank `1.60`, `3/5` `#1` wins, minimax floor `79.0`, `50/50` oracle) vs `top4_github_compilation` (`82.0 / 100`, minimax `69.0`) and `top1_github` (`79.6 / 100`, `48/50` oracle), with `90.2%–99.7%` online Nemhauser–Wolsey optimality certificates.

---

## Install & Platform Versions (Gemini + Codex + Claude + Cursor)

Standalone platform builds for both **`skillcompose`** and **`ml-paper-manifold`** live in [`platforms/`](platforms/README.md) ([`gemini`](platforms/gemini/), [`codex`](platforms/codex/), [`claude`](platforms/claude/), [`cursor`](platforms/cursor/)) as well as workspace auto-discovery directories (`.gemini/skills/`, `.codex/skills/`, `.claude/skills/`, `.cursor/skills/`, `.cursor/rules/`).

```bash
git clone https://github.com/thehalleyyoung/skillcompose.git
cd skillcompose
bash install.sh
```

Installs both `skillcompose` and `ml-paper-manifold` cleanly into:
- **Gemini (`gemini` / Antigravity `agy`)**: `~/.gemini/skills/<skill>` & `~/.gemini/config/skills/<skill>` (`SKILL.md`, `GEMINI.md`, `gemini-extension.json`)
- **Codex (`codex`)**: `${CODEX_HOME:-~/.codex}/skills/<skill>` (`SKILL.md`, `agents/openai.yaml`)
- **Claude (`claude`)**: `~/.claude/skills/<skill>` & `~/.claude/commands/<skill>.md` (`SKILL.md`, `.claude-plugin/plugin.json`)
- **Cursor (`cursor`)**: `~/.cursor/skills/<skill>` (`SKILL.md`, `rules/<skill>.mdc`)

---

## Usage

### Interactive / Agent Invocation (`/skillcompose`)

```text
/skillcompose --n 4 --domain data "sqlite zero downtime schema migration rollback"
/skillcompose --n 4 --domain devops "webhook security audit patch exploit regression"
/skillcompose --n 4 --domain automation --remix-plan-only
/skillcompose --status --wip ./skillremix-wip-20261111T000000Z
```

### Direct Mechanical Manifold & Kleisli Compilation (`compose_skills.py`)

Given any discovered/eligible candidate pool (`candidates.jsonl`), mechanically select, lift to Markov kernels, anti-unify into a Lawvere–Amari manifold atlas, wire, encapsulate, and emit a verified composite skill package (complete with standalone `scripts/project_manifold.py` and `scripts/verify_dominator_gate.py`):

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
python3 metrics/manifold-lift/measure.py
python3 metrics/principled-lift/measure.py
```

---

## Repository Layout

- [`SKILL.md`](SKILL.md) — Agent entry point & protocol for `/skillcompose`
- [`references/theory.md`](references/theory.md) — Complete mathematical, geometric, & categorical-logic derivation
- [`scripts/manifold_engine.py`](scripts/manifold_engine.py) — Conditional Markov kernels over structured outputs, Fisher–Rao metric & Jacobi tangent SVD, Galois conormal invariants, Plotkin–Reynolds anti-unifier, & Čech cocycle checker
- [`scripts/submodular_select.py`](scripts/submodular_select.py) — 6-role noisy-OR + Log-Det Fisher volume submodular selector + JSD/NCD + Nemhauser–Wolsey certificate
- [`scripts/wiring_compiler.py`](scripts/wiring_compiler.py) — 6-operator Kleisli & Sheaf wiring synthesizer and 6-law static theorem verifier
- [`scripts/compose_skills.py`](scripts/compose_skills.py) — End-to-end Lawvere–Amari & Parnas package compiler emitting `MANIFOLD_ATLAS.md`, `project_manifold.py`, and `verify_dominator_gate.py`
- [`scripts/information_gain.py`](scripts/information_gain.py) — Conditional Lempel–Ziv/DEFLATE commit novelty, Attention SNR, and Lyapunov potential $\Phi$
- [`metrics/`](metrics) — 9 reproducible offline verification suites (including [`metrics/manifold-lift/measure.py`](metrics/manifold-lift/measure.py) and [`metrics/principled-lift/measure.py`](metrics/principled-lift/measure.py))
- [`evals/manifold_7family/`](evals/manifold_7family) — 7-family isolated empirical benchmark comparing `concat` ($\bigwedge_i s_i$), `union` ($\bigcup_i s_i$), and `manifold` ($\mathfrak{G}_{\mathcal{M}}$) (`1` call per task $\times$ regime + blind judge & `agy --model claude-sonnet-5-5` runner; see [`RESULTS.md`](evals/manifold_7family/RESULTS.md))

## License

MIT — see [`LICENSE`](LICENSE).
