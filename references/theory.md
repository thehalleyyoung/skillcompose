# Theoretical Foundations of Principled `/skillremix`

Why a naive **"compilation of the best of GitHub"** systematically fails—and how Information Theory, Software Engineering Theory, and Agentic Control Theory turn skill upgrading and remixing into a provable engineering discipline.

---

## 1. Why "A Compilation of the Best of GitHub" Fails: Five Formal Failure Modes

Suppose we want an agent to solve a complex task family $\mathcal{T}$ with ground-truth quality target $Y$ given task input $X$. The standard community approach curates the top-$N$ most popular GitHub / marketplace skills $S_{\text{pop}} = \{s_1, \dots, s_N\}$ and compiles their `SKILL.md` instructions into one mega-skill or thin router. This fails for five mathematical and architectural reasons:

### Failure 1: Popularity-Induced Redundancy Collapse (Submodular Coverage Deficit)
Let $\mathcal{U} = \{u_1, \dots, u_K\}$ be the latent operational stages required to practice $\mathcal{T}$ end-to-end:
1. `spec_grounding` (eliciting/locking preconditions & resolving ambiguity),
2. `synthesis` (constructive generation/transformation),
3. `static_contract` (schema/type/invariant checking),
4. `exec_observation` (running code/queries/experiments against reality),
5. `adversarial_verify` (orthogonal critique & exploit/edge testing),
6. `state_recovery` (idempotent rollback, continuity, checkpointing).

Marketplace install and star counts follow a heavy-tailed distribution skewed toward **entry-stage synthesis** ($u_2$: "write X", "brainstorm X", "generate X"), because entry-stage prompts have the widest casual funnel. Ranking by popularity solves the **modular** objective $\arg\max_{|S|=N} \sum_{s \in S} \text{pop}(s)$, which picks $N$ near-paraphrases of $u_2$ with high pairwise mutual information $I(s_i; s_j) \gg 0$ while leaving stages $u_1, u_3, u_4, u_5, u_6$ uncovered ($I(S_{\text{pop}}; u_k) \approx 0$).

Even surface diversity heuristics (e.g., dissimilar skill-name tokens + distinct repo owners) fail in the opposite direction: an off-domain polysemic skill (`plaid` for "plan/ideation", `storybook` for "story writing", `springboot-verification` for "research verification") has zero name-token overlap with existing picks and therefore scores *maximally diverse* under naive Jaccard!

### Failure 2: Zero Emergent Synergy Under Text Juxtaposition (PID Theorem)
By Williams & Beer's **Partial Information Decomposition (PID)**, the mutual information two skills $(S_1, S_2)$ provide about target outcome $Y$ decomposes into four non-negative atoms:

$$I(S_1, S_2; Y) = \text{Red}(S_1, S_2; Y) + \text{Unq}(S_1; Y \mid S_2) + \text{Unq}(S_2; Y \mid S_1) + \text{Syn}(S_1, S_2; Y)$$

When two GitHub skills are merely concatenated or called sequentially over unstructured chat prose:
- Overlapping best-practice advice lands in $\text{Red}(S_1, S_2; Y)$ (paying context tokens twice for the same bit).
- Independent advice lands in $\text{Unq}(S_i; Y \mid S_j)$ (additive at best).
- **$\text{Syn}(S_1, S_2; Y) = 0$**: Synergistic information is strictly positive *only* when downstream operator $S_2$ conditions on a **bound structural witness** $W = f(X, S_1)$ that $S_2$ could not extract alone and $S_1$ could not actuate alone (analogous to an XOR parity channel). Without typed intermediate representations and cross-artifact pullback checks, "more than the sum of its parts" is impossible.

### Failure 3: The Data Processing Inequality (DPI) in Pure-Prompt Pipelines
For any Markov chain of pure prompt transformations $X \to M_1 \to M_2 \to \dots \to M_k$ that never queries an external deterministic oracle or environment, Shannon's **Data Processing Inequality** guarantees:

$$I(Y^*; M_k) \le I(Y^*; M_{k-1}) \le \dots \le I(Y^*; M_1) \le I(Y^*; X)$$

Chaining prompt-only GitHub skills ("ideate → outline → refine → review → polish") **cannot create ground-truth information** about whether SQL migrations run, exploits fail, citations match tables, or parsers handle edge cases. Each pure-LLM hop introduces lossy re-summarization (context drift) while amplifying model priors (mode collapse). The **only** way to achieve $I(Y^*; M_{k+1}) > I(Y^*; M_k)$ is an **Exogenous Observation Channel** $E_k = \mathcal{O}_{\text{env}}(M_k)$ (a deterministic script, compiler, solver, test runner, or AST/schema verifier) making the transition $(M_k, E_k) \to M_{k+1}$.

### Failure 4: Finite Attention Channel SNR & Parnas Encapsulation Violation
An LLM operating over active prompt context $C$ acts as a finite-precision attention channel. The effective compliance signal-to-noise ratio for critical invariant $c \in S_i$ degrades with total loaded instruction mass and inter-skill rule conflict:

$$\text{SNR}(c \mid C) \propto \frac{w(c)}{\sum_{s \in C} |s|_{\text{tokens}} + \beta \sum_{a < b} \text{Conflict}(s_a, s_b)}$$

Compiling five 500-line GitHub `SKILL.md` files into one prompt dumps 2,500 lines of uncoordinated, partially contradictory directives into working memory—violating **Parnas's (1972) Information Hiding Principle** and causing instruction dropping ("lost in the middle") and style averaging.

### Failure 5: Correlated Self-Grading & Common-Mode False-Done Cascade
Most standalone GitHub skills end with prose self-checks ("verify your code is clean and complete"). When generator $S_{\text{gen}}$ and self-check $S_{\text{check}}$ execute in the same conversational context with write access to the artifact, their error indicators are strongly correlated:

$$\text{Corr}\big(\mathbb{I}[\text{Err}(S_{\text{gen}})],\; \mathbb{I}[\text{Miss}(S_{\text{check}})]\big) \approx 1$$

The blind spot that caused the generator to miss an edge case or hallucinate a denominator is the *same* blind spot active during prose self-review.

---

## 2. Software Engineering Theory: What It *Means* to Combine Skills

In software engineering theory, a skill is **not** a document to concatenate. An agent skill is an **Open Effectful Module (Typed Kleisli Transducer)**:

$$\mathcal{S} = \langle I,\; O,\; P,\; Q,\; \mathcal{F},\; \mathcal{E},\; \mathcal{B} \rangle$$

| Component | Formal Meaning | Software Engineering Principle |
|---|---|---|
| $I, O$ | Typed input & output artifact schemas (named files / JSON contracts) | **Typed Module Interfaces** (not untyped chat history) |
| $P : I \to \mathbb{B}$ | Decidable entry precondition + explicit `ABSTAIN` complement ($\neg P \implies \texttt{ABSTAIN}$) | **Total Input Guarding** (eliminates polysemic misfires) |
| $Q : I \times O \to \mathbb{B}$ | Executable postcondition / deterministic verification script | **Meyer's Design by Contract** (machine-checkable postconditions) |
| $\mathcal{F} = (\mathcal{R}, \mathcal{W}, \text{Eff})$ | Read-set $\mathcal{R}$, write-set $\mathcal{W}$, and side-effect footprint | **Hoare / Reynolds Separation Logic** & frame conditions |
| $\mathcal{E}$ | Typed failure sum: `Ok(O) \| Refuse(code) \| Retry(diag) \| Blocked(dep)` | **Algebraic Error Handling** (exit `2` refusal vs silent partial output) |
| $\mathcal{B}$ | Concise interface in `SKILL.md`; mechanics hidden in `scripts/` & `references/` | **Parnas Information Hiding** & progressive disclosure |

Under this model, **combining skills** means applying **five typed algebraic composition operators**, each carrying a static verification obligation checked by `scripts/wiring_compiler.py`:

### Operator 1: Sequential Kleisli Pipe ($S_2 \circ_\alpha S_1$) — Contract Refinement
Two skills compose sequentially iff there exists a (possibly identity) **Sufficient-Statistic Adapter** $\alpha : O_1 \to I_2$ such that Meyer's Hoare compatibility holds:

$$Q_1(x, y_1) \implies P_2(\alpha(y_1))$$

and $\alpha(y_1)$ strips $S_1$'s internal scratchpad down to the **minimal sufficient statistic** $T(y_1)$ satisfying $I(T(y_1); Y_{\ge 2}) = I(y_1; Y_{\ge 2})$ (**Information Bottleneck**). Subskills are synthesized *specifically* as witness adapters $\alpha$ where $O_1 \neq I_2$, never as boilerplate wrappers.

### Operator 2: Parallel Tensor ($S_1 \otimes S_2$) — Concurrent Separation Logic
Two skills compose in parallel iff their frames are non-interfering:

$$\mathcal{W}(S_1) \cap \mathcal{W}(S_2) = \emptyset \quad \land \quad \mathcal{W}(S_1) \cap \mathcal{R}(S_2) = \emptyset \quad \land \quad \mathcal{W}(S_2) \cap \mathcal{R}(S_1) = \emptyset$$

Read-only critics ($\mathcal{W} = \emptyset$) compose via $\otimes$ freely (ensemble variance reduction); concurrent mutators on overlapping files are statically rejected unless partitioned onto disjoint slices followed by a merge gate.

### Operator 3: Guarded Coproduct ($G \triangleright (S_1 \oplus S_2 \oplus \texttt{ABSTAIN})$) — Behavioral Subtyping
Dispatches mutually exclusive task variants via deterministic guards $g_i(x)$ while enforcing **Liskov Behavioral Subtyping (LSP)**: every branch returns an artifact conforming to the supertype postcondition $Q_{\text{super}}$, or cleanly halts in `ABSTAIN`.

### Operator 4: Orthogonal Feedback Loop ($\mu X.\; \text{Gate}_Q \circ (S_{\text{act}} \leftrightarrows S_{\text{crit}})$) — N-Version Fault Independence
To defeat common-mode failure, every mutating operator $S_{\text{act}}$ ($\mathcal{W} \neq \emptyset$) is paired with an **orthogonal critic / executable gate** $S_{\text{crit}}$ satisfying:
1. **Frame Orthogonality**: $\mathcal{W}(S_{\text{crit}}) = \emptyset$ (critics never rewrite; rewriters never self-certify).
2. **Channel Orthogonality**: $S_{\text{crit}}$ invokes an exogenous executable check $Q$ (test suite, SQLite run, AST check, numerical provenance hash, lexicon/stylometry scanner) rather than re-asking the same prompt "does this look right?".

### Operator 5: Pullback / Invariant Join ($S_1 \times_K S_2$) — Cross-Artifact Consistency
Whenever $S_1$ and $S_2$ materialize coupled views of a shared entity $K$ (e.g., DB migration columns vs OpenAPI fields; narrative outline beats vs chapter prose; epistemic timeline vs character dialogue), composition inserts a **Pullback Reconciler** verifying the commutative projection $\pi_K(O_1) = \pi_K(O_2)$.

---

## 3. Agentic Control Theory: Closed-Loop Forging & MDL Anti-Gaming

### 1. Graph-Dominator Verification Law
Represent the package workflow as a directed control-flow graph $G = (V, E)$ with entry `START` and terminal `DONE`. A package satisfies **Structural False-Done Immunity** iff for every mutator node $m \in V_{\text{mut}}$, there exists an orthogonal gate node $g \in V_{\text{gate}}$ ($\mathcal{W}(g) = \emptyset$, executable $Q_g$) that **post-dominates** $m$ on *every* path $m \leadsto \texttt{DONE}$.

### 2. Causal-DAG Lyapunov Potential $\Phi(x_t)$
Repairing downstream symptoms while upstream contracts are broken causes oscillation. Define the non-negative potential over DAG-ordered quality dimensions $d \in \{1, \dots, D\}$:

$$\Phi(x_t) = \sum_{d=1}^{D} w_d \max\big(0,\; \tau_d - m_d(x_t)\big), \qquad w_{\text{upstream}} > \sum_{d' \in \text{desc}(d)} w_{d'}$$

Hard invariants act as **Control Barrier Functions** (ratchet: $m_d(x_{t+1}) \ge m_d(x_t)$ on guarded dimensions), ensuring $\Phi(x_t)$ decreases monotonically to the verified fixpoint $\Phi(x^*) = 0$.

### 3. Minimum Description Length (MDL) vs. Goodhart Character-Churn Gaming
A raw `chars_changed >= 1000` gate invites Goodhart's Law: verbose prose padding inflates $L(\text{Skill})$ while *decreasing* agent compliance via attention dilution. Principled `/skillremix` pairs product mass with **Incremental Lempel-Ziv Complexity** ($\Delta C_{\text{zlib}} = C(S_{r-1} \Vert \Delta_r) - C(S_{r-1})$, an upper-bound proxy for conditional Kolmogorov information $K(\Delta_r \mid S_{r-1})$) and **Context-SNR Progressive Disclosure** (keeping `SKILL.md` compact while pushing deterministic verification into `scripts/` and deep reference tables into `references/`).

---

## 4. Mapping Theory to Executable `/skillremix` Scripts

| Theoretical Mechanism | Executable Implementation |
|---|---|
| Submodular coverage + JSD redundancy penalty + off-domain divergence | `scripts/submodular_select.py` (and `pick_n_eligible.py --strategy submodular`) |
| Typed Kleisli ports, Separation Logic, Pullbacks, DPI grounding, Dominator proof | `scripts/wiring_compiler.py` (`compile` & `verify`) |
| MDL / LZ compression novelty, Context-SNR, & Lyapunov debt $\Phi$ | `scripts/information_gain.py` (called from `forge_round.sh` & gates) |
| Synergy + algebraic wholeness verification | `scripts/unify_wholeness.py` (`--strict-theory`) + `scripts/ship_check.py` |
