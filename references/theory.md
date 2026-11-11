# Theoretical Foundations of `/skillcompose`

Why a naive **"compilation of the best of GitHub"** systematically fails—and how **Information Theory**, **Software Engineering Theory** (*what it formally means to combine skills*), and **Agentic Control Theory** turn skill composition into a provable engineering discipline.

---

## 1. Five Formal Failure Modes of "A Compilation of the Best of GitHub"

Suppose an agent must solve a complex task family $\mathcal{T}$ with ground-truth target $Y^*$ given task input $X$ and query $Q$. The standard community heuristic selects the top-$N$ most-installed or most-starred GitHub skills $S_{\text{pop}} = \{s_1, \dots, s_N\}$ and concatenates their `SKILL.md` instructions behind a thin router. This fails for five mathematical and architectural reasons:

### Failure 1: Popularity-Induced Redundancy Collapse & Polysemy Traps
Let $\mathcal{U} = \{u_1, \dots, u_6\}$ be the six latent operational capabilities required across an end-to-end engineering or research task:
1. `spec_grounding` (eliciting preconditions, schemas, and resolving specification ambiguity),
2. `synthesis` (constructive code/SQL/prose/plan generation),
3. `static_contract` (type, grammar, AST, and pullback invariant checking),
4. `exec_observation` (running deterministic tests, queries, or harnesses against reality),
5. `adversarial_verify` (orthogonal critique, exploit probing, and anti-slop scanning),
6. `state_recovery` (idempotent rollback, checkpointing, and continuity ledgers).

Marketplace star/install counts follow a heavy-tailed Zipf distribution skewed heavily toward **entry-stage synthesis** ($u_2$: "write X", "brainstorm X", "optimize X"). Ranking by popularity maximizes a **modular** sum $\sum_{s \in S} \text{pop}(s)$, which collapses onto $N$ redundant paraphrases of $u_2$ ($I(s_i; s_j) \gg 0$) while leaving $u_1, u_3, u_4, u_5, u_6$ uncovered. Conversely, surface diversity heuristics (e.g., dissimilar skill-name tokens) actively prefer **off-domain polysemic traps** (`plaid` for "plan", `storybook` for "story writing", `chartjs` for "data") because alien vocabulary has zero token overlap!

`/skillcompose` instead maximizes a **Query-Conditioned Submodular Objective** (`scripts/submodular_select.py`):

$$F(S \mid Q) = \underbrace{\sum_{u \in \mathcal{U}} w_u \left(1 - \prod_{s \in S} (1 - p(u \mid s, Q))\right)}_{M(S \mid Q)\text{ (Monotone Submodular Noisy-OR Coverage)}} + \lambda_{\text{syn}} \text{Syn}(S) - \lambda_{\text{red}} \overline{\text{Sim}}_{\text{JSD+NCD}}(S) - \lambda_{\text{oot}} \sum_{s \in S} \big(D_{\text{off}}(s \parallel Q) + D_{\text{conflict}}(s)\big)$$

where pairwise similarity blends **Jensen–Shannon Divergence** ($1 - \sqrt{\text{JSD}(P_i \parallel P_j)}$) with **Cilibrasi–Vitányi Normalized Compression Distance** ($1 - d_{\text{NCD}}(s_i, s_j)$ via DEFLATE/LZ77, catching reworded/cloned checklists without hand-tuned keywords), and emits an instance-specific **Nemhauser–Wolsey online submodular optimality bound**:

$$M(\text{OPT}_N \mid Q) \le \min_{0 \le t \le N} \left[ M(S_t \mid Q) + \sum_{e \in \text{Top-}N(V \setminus S_t)} \Delta_M(e \mid S_t, Q) \right]$$

### Failure 2: Zero Emergent Synergy Under Text Juxtaposition (PID Theorem)
By Williams & Beer's **Partial Information Decomposition (PID)**, the mutual information two skills $(S_1, S_2)$ provide about $Y^*$ decomposes into:

$$I(S_1, S_2; Y^*) = \text{Red}(S_1, S_2; Y^*) + \text{Unq}(S_1; Y^* \mid S_2) + \text{Unq}(S_2; Y^* \mid S_1) + \text{Syn}(S_1, S_2; Y^*)$$

Concatenating two `SKILL.md` files yields $\text{Syn}(S_1, S_2; Y^*) = 0$: overlapping tips waste context in $\text{Red}$, while unrelated tips sit in $\text{Unq}$. Positive synergy ($\text{Syn} > 0$) emerges *only* when $S_2$ conditions on a **typed structural witness** $\alpha(O_1)$ emitted by $S_1$ (such as a locked Kleene $K_3$ truth table, schema invariant contract, or epistemic scene ledger) that $S_2$ could not infer alone and $S_1$ could not actuate alone.

### Failure 3: The Data Processing Inequality (DPI) in Pure-Prompt Chains
For any Markov chain of pure prompt transformations $Y^* \to X \to M_1 \to M_2 \to \dots \to M_k$ without external environment interaction, Shannon's **Data Processing Inequality** guarantees:

$$I(Y^*; M_k) \le I(Y^*; M_{k-1}) \le \dots \le I(Y^*; M_1) \le I(Y^*; X)$$

Prompt-only skill compilations cannot create ground-truth information about whether SQLite rollbacks preserve foreign keys, exploits fail, contingency tables exhibit Simpson's paradox, or parsers handle missing attributes. Breaking DPI requires an **Exogenous Observation Channel** $E_k = \mathcal{O}_{\text{env}}(M_k)$ (deterministic Python/SQL/AST/test execution) supplying conditional mutual information $I(Y^*; E_k \mid M_k) > 0$.

### Failure 4: Finite Attention Channel SNR & Parnas Violation
An LLM's instruction-following fidelity over active context $C$ degrades as total unencapsulated token mass and inter-skill conflict grow:

$$\text{SNR}(c \mid C) \propto \frac{w(c)}{\sum_{s \in C} |s|_{\text{active}} + \beta \sum_{a < b} \text{Conflict}(s_a, s_b)}$$

Concatenating four verbose GitHub skills inflates `SKILL.md` to $O(\sum |S_i|)$ and violates **Parnas's (1972) Information Hiding Principle**. Worse, if a popular synthesis skill $S_{\text{gen}}$ contains positive examples of an anti-pattern (e.g., contrastive negation `"It wasn't X. It was Y."` or `eval()`) that a downstream critic $S_{\text{gate}}$ forbids ($Q_{\text{gen}} \wedge P_{\text{gate}} = \bot$), the composed prompt fights itself. `/skillcompose` penalizes specification-conflicting exemplars ($D_{\text{conflict}}(s)$) during selection and encapsulates member bodies inside `references/members/<slug>.md`, keeping root `SKILL.md` at $O(N)$.

### Failure 5: Correlated Self-Grading & Common-Mode False-Done
When the mutating agent grades its own output in prose, generator errors and verifier misses share the exact same blind spot ($\text{Corr}(\text{Err}_{\text{gen}}, \text{Miss}_{\text{check}}) \approx 1$).

---

## 2. Software Engineering Theory: What It *Means* to Combine Skills

In software engineering theory, an agent skill is **not** prose to concatenate; it is an **Open Effectful Module (Typed Kleisli Transducer)** over effect monad $\mathcal{M}$ (state + I/O + failure + non-determinism):

$$\mathcal{S} = \langle I,\; O,\; P,\; Q,\; \mathcal{F},\; \mathcal{E},\; \mathcal{B} \rangle$$

- **$I, O$**: Typed input and output artifact interfaces.
- **$P, Q$**: Meyer **Design-by-Contract** preconditions and machine-checkable postconditions, plus Benveniste–Henzinger **Contract Consistency** ($Q_1 \wedge P_2 \neq \bot$).
- **$\mathcal{F} = (\mathcal{R}, \mathcal{W}, \text{Eff})$**: Read-set $\mathcal{R}$ and write-set $\mathcal{W}$ under **Hoare / Reynolds Separation Logic**.
- **$\mathcal{E}$**: Typed failure coproduct (`Ok(O) | Refuse(exit=2) | Retry(diag)`).
- **$\mathcal{B}$**: **Parnas Encapsulation Boundary** (public `SKILL.md` contract vs hidden `references/members/` & `scripts/`).

Combining skills means applying **five algebraic composition operators** statically verified by `scripts/wiring_compiler.py` and materialized by `scripts/compose_skills.py`:

1. **Sequential Kleisli Pipe with Sufficient-Statistic Adapter ($S_2 \circ_\alpha S_1$)**: Valid iff $Q_1(x, y_1) \implies P_2(\alpha(y_1))$, where $\alpha(y_1)$ is the minimal sufficient statistic (`locked_contract.json`), eliminating raw chat-history drift.
2. **Parallel Tensor ($S_1 \otimes S_2$)**: Valid under **Concurrent Separation Logic** iff $\mathcal{W}_1 \cap \mathcal{W}_2 = \emptyset \land \mathcal{W}_1 \cap \mathcal{R}_2 = \emptyset \land \mathcal{W}_2 \cap \mathcal{R}_1 = \emptyset$. Read-only critics ($\mathcal{W} = \emptyset$) compose in parallel safely.
3. **Guarded Coproduct ($G \triangleright (S_1 \oplus S_2 \oplus \texttt{ABSTAIN})$)**: Total intake dispatch satisfying **Liskov Behavioral Subtyping** with explicit exit-`2` `ABSTAIN` on out-of-domain inputs.
4. **Pullback / Invariant Join ($S_1 \times_K S_2$)**: Enforces commutative projection equality $\pi_K(O_1) = \pi_K(O_2)$ across coupled views (SQLite DDL $\leftrightarrow$ v1/v2 Python API; JSON metrics $\leftrightarrow$ Markdown memo tables; RFC grammar $\leftrightarrow$ AST evaluator; epistemic ledger $\leftrightarrow$ scene prose).
5. **Orthogonal Feedback Loop & Post-Dominator Gate ($\mathcal{W}(S_{\text{gate}}) = \emptyset$)**: `compose_skills.py` synthesizes `scripts/verify_dominator_gate.py`, which SHA-256-snapshots protected deliverables before running exogenous checks and fails (`exit 2`) if any critic mutates a target artifact.

---

## 3. Agentic Control Theory: Post-Dominators, Lyapunov Potentials & MDL

1. **Graph Post-Dominator Law**: In the workflow control-flow graph $G = (V, E)$, every mutator $m \in V_{\text{mut}}$ must be **post-dominated** on all paths $m \leadsto \texttt{DONE}$ by a read-only exogenous gate $g \in V_{\text{gate}}$ ($\mathcal{W}(g) = \emptyset$).
2. **Causal-DAG Lyapunov Potential $\Phi(x_t)$**: Weights upstream contract debt strictly above downstream polish debt ($w_{\text{upstream}} > \sum_{d' \in \text{desc}(d)} w_{d'}$) with Control Barrier ratchets preventing regressions on already-passing gates.
3. **Minimum Description Length (MDL) Anti-Padding (`scripts/information_gain.py`)**: Gates iterative forge commits on conditional DEFLATE/Lempel–Ziv complexity density $\Delta C_{\text{zlib}} / |\Delta_r| \ge 0.10$, blocking Goodhart prose bloat.
