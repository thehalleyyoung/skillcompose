# Theoretical Foundations of `/skillcompose`: Kleisli Transducers, Information Theory, and Lawvere–Amari Generative Skill Manifolds

Why neither **"compiling the best of GitHub"** (prompt concatenation $\bigwedge_i s_i$) nor **"routing over a union of remixed skills"** ($\bigcup_i s_i$) captures the capability family underlying observed skills—and how **Conditional Information Geometry**, **Categorical Logic (Lawvere Hyperdoctrines, Galois Closure, Anti-Unification, Sheaf Cohomology)**, **Software Engineering Theory**, and **Agentic Control Theory** synthesize a genuine parameterized generative process.

---

## 1. What a Skill Actually Is: Guarded Conditional Markov Kernels over Structured Outputs

A common informal metaphor describes a meta-skill as *"the manifold underlying a set of skills."* To make this mathematically exact, we must first avoid a category error: **an individual skill is not a manifold.**

Let $\mathcal{X}$ be a typed space of task inputs (workspace states + specifications) and $\mathcal{Y}$ be a space of **structured outputs**—finite relational/algebraic structures over signature $\Sigma_{\mathcal{Y}}$ (multi-file artifact bundles, ASTs, SQL migrations, schemas, execution traces).

**Definition 1.1 (Skill as a Guarded Conditional Generative Kernel).** A skill $s$ is a triple
$$s \;=\; \big(P_s,\; Q_s,\; K_s\big)$$
representing a Kleisli morphism in the constrained Giry–Powerset monad $\mathcal{X} \leadsto \Delta(\mathcal{Y})$:
1. **Input Precondition Guard ($P_s \subseteq \mathcal{X}$):** A decidable predicate in input logic $\mathcal{L}_{\mathcal{X}}$ with total `ABSTAIN` complement ($x \notin P_s \implies s(x) = \texttt{ABSTAIN}$).
2. **Logical Output Specification ($Q_s \in \mathcal{L}_{\mathcal{X} \times \mathcal{Y}}$):** A refinement / Horn theory cutting out, for each $x \in P_s$, the **admissible structured output fiber**:
   $$\mathcal{Y}_s(x) \;=\; \big\{y \in \mathcal{Y} \;:\; (x, y) \models Q_s\big\} \;\subseteq\; \mathcal{Y}.$$
3. **Conditional Generative Process ($K_s : P_s \leadsto \Delta(\mathcal{Y})$):** A stochastic transition kernel mapping each $x \in P_s$ to a probability measure over $\mathcal{Y}$ satisfying **Logical Soundness** ($\operatorname{supp} K_s(\cdot \mid x) \subseteq \mathcal{Y}_s(x)$) and **Realizability** ($Z_s(x) > 0$). In natural exponential-family coordinates over sufficient statistics $\psi : \mathcal{X} \times \mathcal{Y} \to \mathbb{R}^D$:
   $$K_{\eta_s, Q_s}(y \mid x) \;=\; \frac{\mathbb{I}\big[(x, y) \models Q_s\big] \, \exp\!\big(\langle \eta_s,\, \psi(x, y) \rangle\big)}{Z(\eta_s, Q_s; x)}, \qquad Z(\eta_s, Q_s; x) = \sum_{y \in \mathcal{Y}_s(x)} \exp\!\big(\langle \eta_s,\, \psi(x, y) \rangle\big).$$

This unifies the **set-valued logical view** and the **probabilistic generative view**:
- Taking the support functor ($\operatorname{supp} K_s$) or zero-temperature limit recovers the **set-valued relational transducer** $R_s : x \mapsto \mathcal{Y}_s(x) \subseteq \mathcal{Y}$.
- At finite scale, $K_{\eta_s, Q_s}$ is a **point** in the space $\mathfrak{K}(\mathcal{X}, \mathcal{Y})$ of guarded conditional Markov kernels.

**Where the Manifold Lives:** A single skill $s_i$ is **one point** (a single section/kernel) in $\mathfrak{K}(\mathcal{X}, \mathcal{Y})$. Marketplace skills $S = \{s_1, \dots, s_N\}$ for a domain are **finite noisy point samples** drawn from a lower-dimensional **Conditional Statistical–Logical Manifold** $\mathcal{M} \subset \mathfrak{K}(\mathcal{X}, \mathcal{Y})$ parameterized by chart coordinates $\theta \in \Theta$.

---

## 2. Why Concatenation ($\bigwedge_i s_i$), Popularity Top-$N$, and Union ($\bigcup_i s_i$) Fail

Suppose we observe $N$ marketplace skills $S = \{s_1, \dots, s_N\}$. Naive compilation strategies fail for eight formal reasons:

### Failure 1: Constraint-Union Collapse ($Q_i \land Q_j \vdash \bot$) Under Prompt Concatenation
Concatenating $N$ `SKILL.md` files into one mega-prompt asks the agent to satisfy the conjunction $Q_{\text{concat}} = \bigwedge_{i=1}^N Q_i$. Whenever two valid skills $s_i, s_j \in S$ represent distinct specializations of a legitimate design degree of freedom $\xi_a : \mathcal{Y} \to \Theta_a$ (e.g., $\xi_{\text{exec}}(y) = \texttt{streaming\_incremental}$ vs $\xi_{\text{exec}}(y) = \texttt{transactional\_staged}$, or $\xi_{\text{spec}}(y) = \texttt{json\_contract}$ vs $\texttt{formal\_grammar\_adr}$), their conjunction has **empty admissible fiber**:
$$\mathcal{Y}_{Q_i \land Q_j}(x) \;=\; \mathcal{Y}_i(x) \cap \mathcal{Y}_j(x) \;=\; \emptyset \implies Z(\eta, Q_{\text{concat}}; x) = 0.$$
Sampling when $\mathcal{Y}_{\cap}(x) = \emptyset$ forces uncontrolled attention arbitration in which the model silently drops constraints—frequently dropping *universal safety invariants* alongside conflicting style preferences.

### Failure 2: Relational-Union Rank Deficit ($\bigcup_i s_i$ Cannot Recombine Coordinates)
Suppose instead we build a router or mixture over the sampled skills:
$$R_{\text{union}}(x) = \bigcup_{i=1}^N \mathcal{Y}_i(x), \qquad K_{\text{union}}(y \mid x) = \sum_{i=1}^N w_i(x)\, K_i(y \mid x).$$
If the underlying generative family varies along $r$ independent design axes $\Theta = \Theta_1 \times \dots \times \Theta_r$ with $|\Theta_a| = m_a$, $N$ sampled skills cover at most $N$ fibers out of $\prod_{a=1}^r m_a$ combinations. For any task $x^*$ requiring a **recombinant coordinate** $\theta^* = (\theta_1^{(1)}, \theta_2^{(2)}, \dots) \notin \{\theta^{(1)}, \dots, \theta^{(N)}\}$:
$$\mathcal{Y}^*(x^*) \cap \bigcup_{i=1}^N \mathcal{Y}_i(x^*) = \emptyset \implies K_{\text{union}}\!\big(\mathcal{Y}^*(x^*) \mid x^*\big) = 0, \qquad D_{\text{KL}}\!\big(K^*(\cdot \mid x^*) \,\|\, K_{\text{union}}(\cdot \mid x^*)\big) = +\infty.$$
A union of skills memorizes isolated data points; it never learns the coordinate system spanning them.

### Failure 3: Amari $m$-Mixture vs. $e$-Geodesic Curvature Gap
Even on a shared output fiber $\mathcal{Y}_{\mathcal{M}}(x)$, in Amari's **Information Geometry**, the conditional exponential family $\mathcal{M}_e = \{K_\eta(\cdot \mid x)\}$ is dually flat under the $(\nabla^{(e)}, \nabla^{(m)})$ connections:
- The linear mixture $K_{m\text{-mix}}(\cdot \mid x) = \sum_{i=1}^N \lambda_i K_{\eta^{(i)}}(\cdot \mid x)$ follows an **$m$-geodesic**, which **curves out of $\mathcal{M}_e$** whenever $\eta^{(i)} \neq \eta^{(j)}$, producing bimodal mode-switching rather than coherent synthesis.
- The **exponential ($e$-)geodesic** $K_{\eta(\lambda)}(y \mid x) \propto \prod_{i=1}^N K_{\eta^{(i)}}(y \mid x)^{\lambda_i}$ with $\eta(\lambda) = \sum_{i=1}^N \lambda_i \eta^{(i)}$ stays **on $\mathcal{M}_e$** and uniquely solves the **Variational Reverse-KL Barycenter**:
  $$K_{\eta(\lambda)}(\cdot \mid x) \;=\; \arg\min_{q \in \Delta(\mathcal{Y}_{\mathcal{M}}(x))} \sum_{i=1}^N \lambda_i \, D_{\text{KL}}\!\big(q \,\|\, K_{\eta^{(i)}}(\cdot \mid x)\big),$$
  separated from $K_{m\text{-mix}}$ by a strictly positive Bregman divergence gap $D_{\text{KL}}(K_{\eta(\lambda)} \| K_{m\text{-mix}}) > 0$.

### Failure 4: Čech Cohomology Gluing Obstruction ($\delta^0 y \neq 0$) Across Structured Views
When structured output $y$ decomposes over an open cover $\mathcal{U} = \{U_1, \dots, U_m\}$ of coupled facets (e.g., SQL migration $U_1$, API serializer $U_2$, property tests $U_3$), invoking separate skills per facet yields a 0-cochain $(y_u)_{u \in \mathcal{U}} \in C^0(\mathcal{U}, \mathcal{F}_x)$. A globally valid structured output $y \in \Gamma(\mathcal{U}, \mathcal{F}_x)$ exists **iff** the **Čech coboundary** vanishes on every overlap $U_u \cap U_v$:
$$(\delta^0 y)_{uv} \;=\; \rho_{u \to uv}(y_u) \ominus \rho_{v \to uv}(y_v) \;=\; 0.$$
Worse, if three member skills specify pairwise transition maps $(g_{ab}, g_{bc}, g_{ca})$ around a 2-simplex $(U_a, U_b, U_c)$ in the nerve $\mathcal{N}(\mathcal{U})$ with non-trivial **1-cocycle holonomy** $(\delta^1 g)_{abc} = g_{ca} \circ g_{bc} \circ g_{ab} \neq \mathrm{id}$, **no** global structured output exists at all.

### Failure 5: Popularity-Induced Redundancy Collapse & Polysemy Traps
Marketplace install/star rankings optimize the modular sum $\sum_{s \in S} \text{pop}(s)$, collapsing onto $N$ redundant entry-stage synthesis skills ($I(s_i; s_j) \gg 0$) while leaving specification, static contracts, execution observation, adversarial verification, and rollback uncovered—while naive token dissimilarity selects off-domain polysemic traps (`plaid`, `storybook`).

### Failure 6: Zero Emergent PID Synergy Without Bound Structural Witnesses
By Williams & Beer's **Partial Information Decomposition (PID)**,
$$I(S_1, S_2; Y) = \text{Red}(S_1, S_2; Y) + \text{Unq}(S_1; Y \mid S_2) + \text{Unq}(S_2; Y \mid S_1) + \text{Syn}(S_1, S_2; Y).$$
Synergy $\text{Syn}(S_1, S_2; Y) > 0$ requires conditioning downstream operators on typed structural witnesses $W = f(X, S_1)$ and cross-view sheaf restrictions.

### Failure 7: Data Processing Inequality (DPI) Decay in Pure-Prompt Chains
For any Markov chain $Y^* \to X \to M_1 \to \dots \to M_k$ without deterministic environment interaction,
$$I(Y^*; M_k) \le I(Y^*; M_{k-1}) \le \dots \le I(Y^*; X).$$
Escaping DPI requires an **Exogenous Observation Channel** $E_k = \mathcal{O}_{\text{env}}(M_k)$ injecting fresh conditional mutual information $I(Y^*; E_k \mid M_k) > 0$.

### Failure 8: Finite Attention SNR Dilution & Correlated Self-Grading
Dumping raw member prompts inflates denominator context $|C|_{\text{tokens}}$ (violating **Parnas's Information Hiding Principle**), while letting a mutator grade its own output in-context suffers common-mode error correlation $\text{Corr}(\mathbb{I}[\text{Err}(S_{\text{gen}})], \mathbb{I}[\text{Miss}(S_{\text{check}})]) \approx 1$.

---

## 3. Lawvere–Amari Generative Skill Manifolds: Unifying Geometry and Logic

To synthesize a single generative skill $\mathfrak{G}_{\mathcal{M}}$ from sampled skills $S = \{s_1, \dots, s_N\}$ that **encompasses the underlying manifold** while **acting as a rigorous input-to-structured-output transducer**, `/skillcompose` constructs a **Lawvere–Amari Generative Bundle**:
$$\mathfrak{G}_{\mathcal{M}} \;=\; \big\langle \Theta,\; \mathcal{T}_{\mathcal{M}},\; (\bar{\eta}_0, G_F, V),\; \mathcal{N}(\mathcal{U}),\; \sigma^* \big\rangle.$$

### 3.1 Exact Normal–Tangent Duality Between Differential Geometry and Categorical Logic

In differential geometry, a smooth $r$-dimensional submanifold $\mathcal{M} \subset \mathbb{R}^D$ is characterized locally in two dual ways:
- **Implicitly (Conormal Equations $N^*\mathcal{M}$):** as the zero locus $F_\perp(z) = 0$ of $D - r$ invariant constraint equations; violating $F_\perp(z) = 0$ moves **off** the manifold.
- **Parametrically (Tangent Coordinates $T\mathcal{M} = \ker dF_\perp$):** via free chart coordinates $\theta \in \Theta \subseteq \mathbb{R}^r$ parameterizing admissible motions **along** the manifold.

In categorical logic (**Lawvere Hyperdoctrines** $\mathcal{T} : \Theta^{\text{op}} \to \mathbf{Heyt}$), the exact same decomposition arises from **Galois Closure** and **Plotkin–Reynolds Anti-Unification**:

1. **Conormal Bundle $\Longleftrightarrow$ Regularized Galois Invariant Core ($\Phi_{\text{core}} = \text{Th}_{\text{MDL}}(S)$):**
   Consider the syntax–semantics Galois connection $(\text{Th} \dashv \text{Mod})$ between refinement theories $\Gamma \subseteq \mathcal{L}_{\mathcal{X} \times \mathcal{Y}}$ and classes of generative kernels:
   $$\text{Th}(S) = \{\varphi \in \mathcal{L}_{\text{reg}} : \forall s \in S,\; s \models \varphi\}, \qquad \text{Mod}(\Gamma) = \{K \in \mathfrak{K} : \forall \varphi \in \Gamma,\; K \models \varphi\}.$$
   Just as the Zariski closure $V(I(S))$ in algebraic geometry extracts the vanishing polynomial ideal cutting out the variety through data points $S$, $\Phi_{\text{core}}(x, y) = \bigwedge \text{Th}_{\text{MDL}}(S)$ extracts the **universal structural and domain invariants** (exogenous verification, non-silent failure/rollback, Parnas disclosure, shared domain postconditions) satisfied across the family.

2. **Tangent Bundle $\Longleftrightarrow$ Plotkin–Reynolds Anti-Unification ($\sqcup_{\text{lgg}}$) Over Conflicting Clauses:**
   Wherever sampled skills $s_1, \dots, s_N$ specialize distinct or conflicting clauses on axis $a$ ($s_i \models \xi_a(y) \in V_{i,a}$ with $\exists i, j: V_{i,a} \neq V_{j,a}$), **anti-unification** lifts the conflicting locus into a **typed Lawvere fiber variable** $\theta_a \in \Theta_a = \bigcup_{i=1}^N V_{i,a}$ equipped with specialization substitutions $\sigma_i : \theta_a \mapsto V_{i,a}$. This yields the **Indexed Refinement Theory**:
   $$(x, y) \models \mathcal{T}_{\mathcal{M}}(\theta) \iff \underbrace{\Phi_{\text{core}}(x, y)}_{\text{Conormal Laws } N^*\mathcal{M}=0} \;\land\; \bigwedge_{a=1}^{r_{\text{logic}}} \underbrace{\Psi_a\big(x, y;\, \theta_a\big)}_{\text{Tangent Fiber Coordinates } \Theta}.$$

**Theorem 3.1 (Consistent Recombination & Exact Landmark Recovery).** *Let $\mathcal{T}_{\mathcal{M}}(\theta)$ be synthesized via Galois conormal extraction and Plotkin–Reynolds anti-unification over realizable skills $S = \{s_1, \dots, s_N\}$. Then:*
1. **Landmark Pullback Exactness:** *For every observed skill $s_i \in S$, pulling back $\mathcal{T}_{\mathcal{M}}$ along $\sigma_i$ recovers $s_i$'s conormal-guarded theory: $\sigma_i^* \mathcal{T}_{\mathcal{M}} \equiv Q_i \land \Phi_{\text{core}}$.*
2. **Global Consistency (Defeat of Concatenation Collapse):** *Even when $\bigwedge_{i=1}^N Q_i \vdash \bot$ ($\mathcal{Y}_{\cap}(x) = \emptyset$), every coordinate $\theta \in \prod_a \Theta_a$ yields a non-empty structured output fiber $\mathcal{Y}_{\mathcal{T}_{\mathcal{M}}(\theta)}(x) \neq \emptyset$.*
3. **StrictSuperset of Union (Recombinant Generalization):** *Whenever $\ge 2$ independent chart axes vary across $S$, $\bigcup_{\theta \in \Theta} \mathcal{Y}_{\mathcal{T}_{\mathcal{M}}(\theta)}(x) \supsetneq \bigcup_{i=1}^N \mathcal{Y}_i(x)$, enabling synthesis of structured outputs unreachable by any single member or mixture.*

### 3.2 Amari Conditional Fisher–Rao Geometry & Tangent Geodesic Basis

On the continuous parameter side, each lifted skill $s_i$ induces natural parameters $\eta^{(i)} \in \mathbb{R}^D$ around the **$e$-geodesic barycenter** $\bar{\eta}_0 = \frac{1}{N} \sum_{i=1}^N \eta^{(i)}$. Equipping $\mathcal{M}$ with the **Conditional Fisher–Rao Metric Tensor**:
$$G_F(\bar{\eta}_0) \;=\; \mathbb{E}_{x \sim \mu}\!\left[\nabla_\eta^2 \log Z(\bar{\eta}_0, \mathcal{T}_{\mathcal{M}}; x)\right] \;=\; \mathbb{E}_{x \sim \mu}\!\left[\operatorname{Cov}_{y \sim K_{\bar{\eta}_0}(\cdot \mid x)}\!\big(\psi(x, y)\big)\right] \;\succ\; 0,$$
`scripts/manifold_engine.py` performs exact symmetric Jacobi eigendecomposition on the $G_F$-whitened empirical tangent scatter matrix $S_W = \frac{1}{N}\sum_{i=1}^N G_F^{1/2}(\eta^{(i)} - \bar{\eta}_0)(\eta^{(i)} - \bar{\eta}_0)^\top G_F^{1/2} = U \Lambda U^\top$, yielding $G_F$-orthonormal **principal geodesic generators** $v_k = G_F^{-1/2} u_k$ ($\langle v_a, G_F v_b \rangle = \delta_{ab}$) and **Participation-Ratio Intrinsic Dimension** $d_{\text{eff}} = \frac{(\sum_k \lambda_k)^2}{\sum_k \lambda_k^2}$.

Given any unseen task input $x \in \mathcal{X}$, the **Inverse Chart Encoder** $\sigma^* : \mathcal{X} \to \Theta$ (`project_manifold.py`):
1. Evaluates the **Conormal Domain Guard** $P_{\mathcal{M}}(x)$, halting with exit `2` (`ABSTAIN_OFF_MANIFOLD`) on polysemic/alien triggers.
2. Projects $x$ onto Fisher tangent coordinates $\theta_{\text{cont}}^*(x) = U^\top G_F^{1/2}(\hat{\eta}(x) - \bar{\eta}_0)$ (within Riemannian trust radius $\|\theta_{\text{cont}}^*\|_2 \le R$) and resolves discrete fiber coordinates $\theta_{\text{logic}}^*(x) \in \Theta$.
3. Instantiates the synthesized conditional Markov kernel $K_{\theta^*(x)}(y \mid x)$ at $\eta^*(x) = \bar{\eta}_0 + \sum_{k=1}^r \theta_{\text{cont}, k}^*(x) v_k$ over $\mathcal{Y}_{\mathcal{T}_{\mathcal{M}}(\theta_{\text{logic}}^*(x))}(x)$.

### 3.3 Kiefer–Wolfowitz Optimal Experimental Design: Submodular Log-Det Fisher Volume

To reconstruct a $d$-dimensional tangent space $T_{\bar{\eta}_0}\mathcal{M}$ from $N$ chosen skills, covering pipeline roles alone is insufficient—the chosen landmarks must **geometrically span** $T_{\bar{\eta}_0}\mathcal{M}$. `scripts/submodular_select.py` augments noisy-OR role coverage with the **D-Optimal Fisher Log-Determinant Volume**:
$$V_{\text{Fisher}}(S) \;=\; \frac{1}{2} \log \det\!\left(I_D + \alpha \sum_{s \in S} \tilde{\psi}(s)\tilde{\psi}(s)^\top\right), \qquad \tilde{\psi}(s) = G_F(0)^{1/2}\eta(s).$$

**Theorem 3.2 (Monotone Submodularity of Fisher Spanning Volume).** *By Schur complement, for any $S \subseteq T$ and $e \notin T$,*
$$V_{\text{Fisher}}(S \cup \{e\}) - V_{\text{Fisher}}(S) \;=\; \frac{1}{2}\log\!\Big(1 + \alpha\, \tilde{\psi}(e)^\top \big(I_D + \alpha \tilde{\Psi}_S^\top \tilde{\Psi}_S\big)^{-1} \tilde{\psi}(e)\Big) \;\ge\; V_{\text{Fisher}}(T \cup \{e\}) - V_{\text{Fisher}}(T) \;\ge\; 0$$
*because $A_S = I_D + \alpha \tilde{\Psi}_S^\top \tilde{\Psi}_S \preceq A_T \implies A_S^{-1} \succeq A_T^{-1}$ in the Loewner positive-definite order. Consequently, $M_{\text{total}}(S) = M_{\text{role}}(S) + \gamma V_{\text{Fisher}}(S)$ is strictly monotone submodular, preserving both the worst-case $(1 - 1/e)$ guarantee and the online Nemhauser–Wolsey optimality certificate.*

### 3.4 Presheaves of Structured Outputs & Čech Cohomology Gluing

Structured outputs $y \in \mathcal{Y}$ form sections of a presheaf $\mathcal{F}_x$ over an open cover $\mathcal{U} = \{U_1, \dots, U_m\}$ of domain views, with nerve $\mathcal{N}(\mathcal{U})$:
- **Static 1-Cocycle Exactness ($\delta^1 = 0$):** On every 2-simplex triangle $(U_a, U_b, U_c)$ in $\mathcal{N}(\mathcal{U})$, `wiring_compiler.py` verifies loop holonomy $g_{ca} \circ g_{bc} \circ g_{ab} = \mathrm{id}$ (`manifold_sheaf_exactness`).
- **Runtime 0-Coboundary Enforcement ($\Gamma(\mathcal{U}, \mathcal{F}_x) = \ker \delta^0$):** `verify_dominator_gate.py --glue` checks $(\delta^0 y)_{uv} = \rho_{u \to uv}(y_u) \ominus \rho_{v \to uv}(y_v) = 0$ across materialized JSON/artifact views, rejecting drifted multi-file outputs with exit `2`.

---

## 4. Software Engineering Kleisli Composition & Agentic Control Laws

Each module inside the manifold-parameterized workflow remains an **Open Effectful Kleisli Transducer** $\mathcal{S} = \langle I, O, P, Q, \mathcal{F}, \mathcal{E}, \mathcal{B} \rangle$ wired via **six algebraic operators** checked by `scripts/wiring_compiler.py`:

1. **Lawvere–Amari Chart Projection ($\sigma^* : \mathcal{X} \to \Theta$):** Projects raw input onto contradiction-free fiber coordinates $\theta^*(x)$ and halts with exit-`2` `ABSTAIN_OFF_MANIFOLD` outside the conormal domain guard.
2. **Sequential Kleisli Pipe ($S_2 \circ_\alpha S_1$):** Enforces Meyer Hoare refinement $Q_1(x, y_1) \implies P_2(\alpha(y_1))$ via minimal sufficient-statistic adapters $\alpha$.
3. **Parallel Tensor ($S_1 \otimes S_2$):** Enforces Concurrent Separation Logic frame disjointness $\mathcal{W}_1 \cap (\mathcal{W}_2 \cup \mathcal{R}_2) = \emptyset$ and $\mathcal{W}_2 \cap \mathcal{R}_1 = \emptyset$.
4. **Guarded Coproduct ($G \triangleright (S_1 \oplus S_2 \oplus \texttt{ABSTAIN})$):** Total routing with Liskov Behavioral Subtyping.
5. **Sheaf Equalizer / Pullback Join ($\Gamma(\mathcal{U}, \mathcal{F}) = \ker \delta^0$):** Enforces $\delta^1 = 0$ statically and $\pi_K(O_u) = \pi_K(O_v)$ dynamically across overlapping artifact views.
6. **Post-Dominator Orthogonal Feedback Loop ($\mu X.\; \text{Gate}_Q \circ (S_{\text{act}} \leftrightarrows S_{\text{crit}})$):** Every mutator node $m \in V_{\text{mut}}$ is post-dominated on all paths to `DONE` by a read-only exogenous gate ($\mathcal{W}(g) = \emptyset$, SHA-256 verified) governed by a DAG-ordered **Lyapunov potential** $\Phi(x_t)$ and **Conditional Lempel–Ziv MDL** anti-padding (`info_density >= 0.10`).

---

## 5. Mapping Theory to Executable `/skillcompose` Scripts & Proof Suites

| Theoretical Mechanism | Executable Implementation | Reproducible Verification Suite |
|---|---|---|
| Guarded Markov kernels over 648 structured outputs, Conditional Fisher–Rao metric $G_F$, Galois conormal core, Plotkin–Reynolds anti-unification $\sqcup_{\text{lgg}}$, Čech cocycle checker | `scripts/manifold_engine.py` | `metrics/manifold-lift/measure.py` |
| Monotone submodular Noisy-OR + Log-Det Fisher volume $V_{\text{Fisher}}(S)$ + JSD/NCD anti-redundancy + Nemhauser–Wolsey certificate | `scripts/submodular_select.py` | `metrics/principled-lift/measure.py`, `metrics/manifold-lift/measure.py` |
| 6-operator Kleisli + Sheaf wiring compiler & 6-theorem static verifier (`type_safety`, `separation_logic`, `dpi_exogenous_grounding`, `dominator_orthogonality`, `parnas_encapsulation`, `manifold_sheaf_exactness`) | `scripts/wiring_compiler.py` | `metrics/principled-lift/measure.py`, `metrics/manifold-lift/measure.py` |
| End-to-end composite manifold compiler emitting `MANIFOLD_ATLAS.md`, standalone `project_manifold.py`, & sheaf/SHA-256 `verify_dominator_gate.py` | `scripts/compose_skills.py` | `metrics/manifold-lift/measure.py`, `metrics/principled-lift/measure.py` |
| Conditional DEFLATE/LZ novelty, Attention Channel SNR, & Lyapunov debt $\Phi$ | `scripts/information_gain.py` | `metrics/principled-lift/measure.py` |
