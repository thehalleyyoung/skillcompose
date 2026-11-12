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

Suppose we observe $N$ marketplace skills $S = \{s_1, \dots, s_N\}$ under task query $Q$. Naive compilation strategies fail for eight formal reasons:

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

### Failure 5: Popularity-Induced Redundancy Collapse, Polysemy Traps & Exemplar Conflicts
Marketplace install/star rankings optimize the modular sum $\sum_{s \in S} \text{pop}(s)$, collapsing onto $N$ redundant entry-stage synthesis skills ($I(s_i; s_j) \gg 0$) across the 6 latent roles (`spec_grounding`, `synthesis`, `static_contract`, `exec_observation`, `adversarial_verify`, `state_recovery`), while naive token dissimilarity prefers off-domain polysemic traps (`plaid` for "plan", `storybook` for "story") or skills whose positive exemplars teach anti-patterns ($D_{\text{conflict}}(s) > 0$) that contradict downstream critics ($Q_{\text{gen}} \wedge P_{\text{gate}} = \bot$).

### Failure 6: Zero Emergent PID Synergy Without Bound Structural Witnesses
By Williams & Beer's **Partial Information Decomposition (PID)**,
$$I(S_1, S_2; Y^*) = \text{Red}(S_1, S_2; Y^*) + \text{Unq}(S_1; Y^* \mid S_2) + \text{Unq}(S_2; Y^* \mid S_1) + \text{Syn}(S_1, S_2; Y^*).$$
Synergy $\text{Syn}(S_1, S_2; Y^*) > 0$ requires conditioning downstream operators on typed structural witnesses $\alpha(O_1)$ and cross-view sheaf restrictions.

### Failure 7: Data Processing Inequality (DPI) Decay in Pure-Prompt Chains
For any Markov chain $Y^* \to X \to M_1 \to \dots \to M_k$ without deterministic environment interaction,
$$I(Y^*; M_k) \le I(Y^*; M_{k-1}) \le \dots \le I(Y^*; X).$$
Escaping DPI requires an **Exogenous Observation Channel** $E_k = \mathcal{O}_{\text{env}}(M_k)$ injecting fresh conditional mutual information $I(Y^*; E_k \mid M_k) > 0$.

### Failure 8: Finite Attention SNR Dilution & Correlated Self-Grading
Dumping raw member prompts inflates denominator context $|C|_{\text{tokens}}$ (violating **Parnas's Information Hiding Principle**), while letting a mutator grade its own output in-context suffers common-mode error correlation $\text{Corr}(\mathbb{I}[\text{Err}(S_{\text{gen}})], \mathbb{I}[\text{Miss}(S_{\text{check}})]) \approx 1$.

---

## 3. Lawvere–Amari Generative Skill Manifolds: Unifying Geometry and Logic

To synthesize a single generative skill $\mathfrak{G}_{\mathcal{M}}$ from sampled skills $S = \{s_1, \dots, s_N\}$ that **encompasses the underlying manifold** while **acting as a rigorous input-to-structured-output transducer**, `/skillcompose` constructs a **Lawvere–Amari Generative Bundle**:
$$\mathfrak{G}_{\mathcal{M}}(D) \;=\; \big\langle \Theta,\; \mathcal{T}_{\mathcal{M}},\; (\bar{\eta}_0, G_F, V),\; \mathcal{N}(\mathcal{U}),\; \sigma^*,\; \mathcal{A}_{\mathcal{M}}(D) \big\rangle,$$
where the optional desired argument theory $D$ (empty by default) is defined in §3.5. It is part of the composed object, not a side channel around it.

### 3.1 Exact Normal–Tangent Duality Between Differential Geometry and Categorical Logic

In differential geometry, a smooth $r$-dimensional submanifold $\mathcal{M} \subset \mathbb{R}^D$ is characterized locally in two dual ways:
- **Implicitly (Conormal Equations $N^*\mathcal{M}$):** as the zero locus $F_\perp(z) = 0$ of $D - r$ invariant constraint equations; violating $F_\perp(z) = 0$ moves **off** the manifold.
- **Parametrically (Tangent Coordinates $T\mathcal{M} = \ker dF_\perp$):** via free chart coordinates $\theta \in \Theta \subseteq \mathbb{R}^r$ parameterizing admissible motions **along** the manifold.

In categorical logic (**Lawvere Hyperdoctrines** $\mathcal{T} : \Theta^{\text{op}} \to \mathbf{Heyt}$), the exact same decomposition arises from **Galois Closure** and **Plotkin–Reynolds Anti-Unification**:

1. **Conormal Bundle $\Longleftrightarrow$ Regularized Galois Invariant Core ($\Phi_{\text{core}} = \text{Th}_{\text{MDL}}(S)$):**
   Consider the syntax–semantics Galois connection $(\text{Th} \dashv \text{Mod})$ between refinement theories $\Gamma \subseteq \mathcal{L}_{\mathcal{X} \times \mathcal{Y}}$ and classes of generative kernels:
   $$\text{Th}(S) = \{\varphi \in \mathcal{L}_{\text{reg}} : \forall s \in S,\; s \models \varphi\}, \qquad \text{Mod}(\Gamma) = \{K \in \mathfrak{K} : \forall \varphi \in \Gamma,\; K \models \varphi\}.$$
   Just as the Zariski closure $V(I(S))$ in algebraic geometry extracts the vanishing polynomial ideal cutting out the variety through data points $S$, $\Phi_{\text{core}}(x, y) = \bigwedge \text{Th}_{\text{MDL}}(S)$ extracts the **universal structural and domain invariants** (exogenous verification, non-silent failure/rollback, idempotence $f \circ f = f$, zero TOCTOU, Parnas disclosure, shared domain postconditions) satisfied across the family.

2. **Tangent Bundle $\Longleftrightarrow$ Plotkin–Reynolds Anti-Unification ($\sqcup_{\text{lgg}}$) Over Conflicting Clauses:**
   Wherever sampled skills $s_1, \dots, s_N$ specialize distinct or conflicting clauses on axis $a$ ($s_i \models \xi_a(y) \in V_{i,a}$ with $\exists i, j: V_{i,a} \neq V_{j,a}$), **anti-unification** lifts the conflicting locus into a **typed Lawvere fiber variable** $\theta_a \in \Theta_a = \bigcup_{i=1}^N V_{i,a}$ equipped with specialization substitutions $\sigma_i : \theta_a \mapsto V_{i,a}$. This yields the **Indexed Refinement Theory**:
   $$(x, y) \models \mathcal{T}_{\mathcal{M}}(\theta) \iff \underbrace{\Phi_{\text{core}}(x, y)}_{\text{Conormal Laws } N^*\mathcal{M}=0} \;\land\; \bigwedge_{a=1}^{r_{\text{logic}}} \underbrace{\Psi_a\big(x, y;\, \theta_a\big)}_{\text{Tangent Fiber Coordinates } \Theta}.$$

**Theorem 3.1 (Consistent Recombination & Exact Landmark Recovery).** *Let $\mathcal{T}_{\mathcal{M}}(\theta)$ be synthesized via Galois conormal extraction and Plotkin–Reynolds anti-unification over realizable skills $S = \{s_1, \dots, s_N\}$. Then:*
1. **Landmark Pullback Exactness:** *For every observed skill $s_i \in S$, pulling back $\mathcal{T}_{\mathcal{M}}$ along $\sigma_i$ recovers $s_i$'s conormal-guarded theory: $\sigma_i^* \mathcal{T}_{\mathcal{M}} \equiv Q_i \land \Phi_{\text{core}}$.*
2. **Global Consistency (Defeat of Concatenation Collapse):** *Even when $\bigwedge_{i=1}^N Q_i \vdash \bot$ ($\mathcal{Y}_{\cap}(x) = \emptyset$), every coordinate $\theta \in \prod_a \Theta_a$ yields a non-empty structured output fiber $\mathcal{Y}_{\mathcal{T}_{\mathcal{M}}(\theta)}(x) \neq \emptyset$.*
3. **Strict Superset of Union (Recombinant Generalization):** *Whenever $\ge 2$ independent chart axes vary across $S$, $\bigcup_{\theta \in \Theta} \mathcal{Y}_{\mathcal{T}_{\mathcal{M}}(\theta)}(x) \supsetneq \bigcup_{i=1}^N \mathcal{Y}_i(x)$, enabling synthesis of structured outputs unreachable by any single member or mixture.*

### 3.2 Amari Conditional Fisher–Rao Geometry & Tangent Geodesic Basis

On the continuous parameter side, each lifted skill $s_i$ induces natural parameters $\eta^{(i)} \in \mathbb{R}^D$ around the **$e$-geodesic barycenter** $\bar{\eta}_0 = \frac{1}{N} \sum_{i=1}^N \eta^{(i)}$. Equipping $\mathcal{M}$ with the **Conditional Fisher–Rao Metric Tensor**:
$$G_F(\bar{\eta}_0) \;=\; \mathbb{E}_{x \sim \mu}\!\left[\nabla_\eta^2 \log Z(\bar{\eta}_0, \mathcal{T}_{\mathcal{M}}; x)\right] \;=\; \mathbb{E}_{x \sim \mu}\!\left[\operatorname{Cov}_{y \sim K_{\bar{\eta}_0}(\cdot \mid x)}\!\big(\psi(x, y)\big)\right] \;\succ\; 0,$$
`scripts/manifold_engine.py` performs exact symmetric Jacobi eigendecomposition on the $G_F$-whitened empirical tangent scatter matrix $S_W = \frac{1}{N}\sum_{i=1}^N G_F^{1/2}(\eta^{(i)} - \bar{\eta}_0)(\eta^{(i)} - \bar{\eta}_0)^\top G_F^{1/2} = U \Lambda U^\top$, yielding $G_F$-orthonormal **principal geodesic generators** $v_k = G_F^{-1/2} u_k$ ($\langle v_a, G_F v_b \rangle = \delta_{ab}$) and **Participation-Ratio Intrinsic Dimension** $d_{\text{eff}} = \frac{(\sum_k \lambda_k)^2}{\sum_k \lambda_k^2}$.

Given any unseen task input $x \in \mathcal{X}$, the **Inverse Chart Encoder** $\sigma^* : \mathcal{X} \to \Theta$ (`project_manifold.py`):
1. Evaluates the **Conormal Domain Guard** $P_{\mathcal{M}}(x)$, halting with exit `2` (`ABSTAIN_OFF_MANIFOLD`) on polysemic/alien triggers.
2. Projects $x$ onto Fisher tangent coordinates $\theta_{\text{cont}}^*(x) = U^\top G_F^{1/2}(\hat{\eta}(x) - \bar{\eta}_0)$ (within Riemannian trust radius $\|\theta_{\text{cont}}^*\|_2 \le R$) and resolves discrete fiber coordinates $\theta_{\text{logic}}^*(x) \in \Theta$.
3. Instantiates the synthesized conditional Markov kernel $K_{\theta^*(x)}(y \mid x)$ at $\eta^*(x) = \bar{\eta}_0 + \sum_{k=1}^r \theta_{\text{cont}, k}^*(x) v_k$ over $\mathcal{Y}_{\mathcal{T}_{\mathcal{M}}(\theta_{\text{logic}}^*(x))}(x)$.

### 3.3 Query-Conditioned Optimal Experimental Design: Submodular Noisy-OR + Log-Det Fisher Volume

To reconstruct a $d$-dimensional tangent space $T_{\bar{\eta}_0}\mathcal{M}$ from $N$ chosen skills under query $Q$, `scripts/submodular_select.py` combines query-conditioned noisy-OR role coverage $M_{\text{role}}(S \mid Q) = \sum_{u \in \mathcal{U}} w_u \big(1 - \prod_{s \in S}(1 - p(u \mid s, Q))\big)$ with the **D-Optimal Fisher Log-Determinant Volume**:
$$V_{\text{Fisher}}(S) \;=\; \frac{1}{2} \log \det\!\left(I_D + \alpha \sum_{s \in S} \tilde{\psi}(s)\tilde{\psi}(s)^\top\right), \qquad \tilde{\psi}(s) = G_F(0)^{1/2}\eta(s),$$
penalized by blended JSD + Cilibrasi–Vitányi NCD similarity $\overline{\text{Sim}}_{\text{JSD+NCD}}(S)$ and off-domain + exemplar conflict divergence $\sum_{s \in S}(D_{\text{off}}(s \parallel Q) + D_{\text{conflict}}(s))$.

**Theorem 3.2 (Monotone Submodularity of Joint Coverage + Fisher Volume).** *By Schur complement, for any $S \subseteq T$ and $e \notin T$,*
$$V_{\text{Fisher}}(S \cup \{e\}) - V_{\text{Fisher}}(S) \;=\; \frac{1}{2}\log\!\Big(1 + \alpha\, \tilde{\psi}(e)^\top \big(I_D + \alpha \tilde{\Psi}_S^\top \tilde{\Psi}_S\big)^{-1} \tilde{\psi}(e)\Big) \;\ge\; V_{\text{Fisher}}(T \cup \{e\}) - V_{\text{Fisher}}(T) \;\ge\; 0$$
*because $A_S = I_D + \alpha \tilde{\Psi}_S^\top \tilde{\Psi}_S \preceq A_T \implies A_S^{-1} \succeq A_T^{-1}$ in the Loewner positive-definite order. Consequently, $M_{\text{total}}(S \mid Q) = M_{\text{role}}(S \mid Q) + \gamma V_{\text{Fisher}}(S)$ is strictly monotone submodular, preserving both the worst-case $(1 - 1/e)$ guarantee and the online Nemhauser–Wolsey optimality certificate.*

### 3.4 Presheaves of Structured Outputs & Čech Cohomology Gluing

Structured outputs $y \in \mathcal{Y}$ form sections of a presheaf $\mathcal{F}_x$ over an open cover $\mathcal{U} = \{U_1, \dots, U_m\}$ of domain views, with nerve $\mathcal{N}(\mathcal{U})$:
- **Static 1-Cocycle Exactness ($\delta^1 = 0$):** On every 2-simplex triangle $(U_a, U_b, U_c)$ in $\mathcal{N}(\mathcal{U})$, `wiring_compiler.py` verifies loop holonomy $g_{ca} \circ g_{bc} \circ g_{ab} = \mathrm{id}$ (`manifold_sheaf_exactness`).
- **Runtime 0-Coboundary Enforcement ($\Gamma(\mathcal{U}, \mathcal{F}_x) = \ker \delta^0$):** `verify_dominator_gate.py --glue` checks $(\delta^0 y)_{uv} = \rho_{u \to uv}(y_u) \ominus \rho_{v \to uv}(y_v) = 0$ across materialized JSON/artifact views, rejecting drifted multi-file outputs with exit `2`.

### 3.5 What the final skill takes, and what it is able to take

The object produced by composition is itself a skill, so it has an input signature. Each landmark $s_i$ already has one. Write $T_i$ for the arguments $s_i$ **takes** (the precondition $P_i$ fails until they are instantiated) and $B_i \supseteq T_i$ for the arguments $s_i$ is **able to take** (supplying one stays inside $P_i$; omitting an argument in $B_i \setminus T_i$ is still a legal input).

Member signatures compose by the same normal/tangent split as output clauses (§3.1):

- **Conormal input core.** $T_\cap = \bigcap_{i=1}^N T_i$ is the set of arguments every landmark takes. The final skill takes them. Dropping one would delete a precondition the whole family shares.
- **Tangent input axes.** $B_\cup = \bigcup_{i=1}^N B_i$ is the set of arguments some landmark is able to take. Plotkin–Reynolds anti-unification $\sqcup_{\text{lgg}}$ lifts the ones that landmarks disagree on (required here, hard-coded there, absent elsewhere) into chart variables. That is what it means for the final skill to be *able* to take them: each landmark pullback $\sigma_i$ puts back the constant that landmark had specialized.

A caller often knows the interface they want back before the landmarks are fused. That knowledge is an **optional desired argument theory**
$$D \;=\; (D_{\text{take}},\, D_{\text{able}}), \qquad D_{\text{take}} \subseteq D_{\text{able}},$$
with either component allowed to be empty.

- $D_{\text{take}}$: arguments the final skill should **take**.
- $D_{\text{able}}$: arguments the final skill should **be able to take**.

$D$ is not the discovery query $Q$ and not a meta-control flag (`--n`, `--domain`, `--pin`, …). $Q$ selects landmarks. $D$ fixes the arity of the skill those landmarks must become. Folding $D$ into $Q$ would turn a typed signature into bag-of-words context and would let an interface constraint masquerade as a control flag. The reference parser therefore keeps them apart: `--args` is recorded as `composed_args` and classified into `desired_interface`. An unmarked name lands in $D_{\text{able}}$. A name marked `take:` also lands in $D_{\text{take}}$ (and therefore in $D_{\text{able}}$, since taking implies being able to take).

**Definition 3.3 (Composed argument interface).**
$$\mathcal{A}_{\mathcal{M}}(D) \;=\; \big( T_\cap \cup D_{\text{take}},\; B_\cup \cup D_{\text{able}} \big).$$
The final skill is the Kleisli morphism whose precondition requires the first component and accepts the second. An argument in the second component but not the first may be absent; that absence is an optional chart point, not an off-manifold input.

**Corollary 3.1 (Empty desire, required interface, fresh axes).** *Let $\mathcal{A}_{\mathcal{M}}(D)$ be as above, and assume no demanded value contradicts $\Phi_{\text{core}}$. Then:*
1. **Empty desire is anti-unification.** *$D = (\emptyset, \emptyset)$ yields $\mathcal{A}_{\mathcal{M}}(D) = (T_\cap, B_\cup)$, the signature already latent in the landmarks.*
2. **Taking implies being able to take.** *$T_\cap \cup D_{\text{take}} \subseteq B_\cup \cup D_{\text{able}}$.*
3. **Landmark recovery.** *Pulling $\mathcal{A}_{\mathcal{M}}(D)$ back along $\sigma_i$ instantiates every newly required argument at the constant $s_i$ had hard-coded, and forgets every optional argument $s_i$ did not mention, recovering $P_i$. This is the input half of Theorem 3.1.*
4. **A new able-argument is a new chart coordinate.** *A name in $D_{\text{able}} \setminus B_\cup$ extends $\Theta$ by a free input axis, and $\mathcal{T}_{\mathcal{M}}$ may depend on it. If a demanded value together with $\Phi_{\text{core}}$ derives $\bot$, the conormal guard fails and composition abstains (`ABSTAIN_OFF_MANIFOLD`, exit 2): the requested interface does not lie on $\mathcal{M}$.*

Example. For an end-to-end fantasy-novel skill the caller may pass $D_{\text{able}} = \{\texttt{author-persona}, \texttt{premise}\}$ and $D_{\text{take}} = \emptyset$. The finished skill is able to take both, and it still runs when they are omitted. Marking premise as taken ($D_{\text{take}} = \{\texttt{premise}\}$) puts premise in the precondition: a later invocation without a premise is outside $P_{\mathcal{M}}$.

### 3.6 What a skill carries: specification, channels, and modules

Definition 1.1 describes a skill by its kernel. A packaged skill realizes that kernel from more than its `SKILL.md`. It also realizes it from the files that text sends the agent to. Theorem 3.1 is exact about the theory $Q_i$. Without the files below it says nothing about the kernel $K_i$ an agent actually runs, and that gap shows up in practice: a recomposition that keeps every member's specification but drops the scripts they invoke passes every static check and still runs a different skill.

**Definition 3.4 (Carrier and reference closure).** A package is a pair $p = (\varsigma_p, C_p)$. Here $\varsigma_p$ is the specification text and $C_p$ is a finite set of files $(\text{path}, \text{bytes})$, split into
- **executable channels** $E_p \subseteq C_p$ (scripts the text tells the agent to run; each one is an exogenous observation $\mathcal{O}_f$ in the sense of Failure 7), and
- **reference modules** $R_p = C_p \setminus E_p$ (documents the text defers to by progressive disclosure).

Write $\varsigma \to f$ when the text names file $f$ and $f$ exists in the member's repository, and extend $\to$ to files that name other files. The **reference closure** $\operatorname{cl}(s)$ is the smallest set that contains the member's `scripts/` and `references/` trees and is closed under $\to$. It may include files outside the member's folder, for example a script under the repository root.

*Reference locality hypothesis.* An agent running $p$ reads and executes only files reachable from $\varsigma_p$ by $\to$, so $K_p = K[\varsigma_p, \operatorname{cl}(p)]$.

Packages are ordered by carrier inclusion: $p \sqsubseteq p'$ iff $C_p \subseteq C_{p'}$ as sets of $(\text{path}, \text{bytes})$ pairs, ignoring paths the installer regenerates from the specification (host manifests).

**Proposition 3.2 (Carrier closure, channel loss, and installation as join).** *Assume reference locality. Let $\mathfrak{G}_{\mathcal{M}}$ be composed from $S = \{s_1, \dots, s_N\}$, and let $\iota_i$ relocate member $i$'s files injectively into the package, rewriting the references among them.*
1. **Kernel-exact pullback.** *$\sigma_i^* \mathfrak{G}_{\mathcal{M}}$ realizes $K_i$, and not only $Q_i \land \Phi_{\text{core}}$, if $\iota_i(\operatorname{cl}(s_i)) \subseteq C_{\mathcal{M}}$ byte for byte.*
2. **Dropping a channel loses information.** *If an executable channel $f \in \operatorname{cl}(s_i)$ is missing from $C_{\mathcal{M}}$, its observation becomes constant, and the information a run can reach falls by*
   $$I(Y^*;\, M, E_{C}) - I(Y^*;\, M, E_{C \setminus \{f\}}) \;=\; I(Y^*;\, E_f \mid M, E_{C \setminus \{f\}}) \;\ge\; 0,$$
   *with strict inequality whenever $f$ is informative given the rest. That is the DPI decay of Failure 7, reintroduced by packaging.*
3. **Files outside the closure are free to omit.** *A file not in $\operatorname{cl}(s_i)$ never enters $K_i$. Omitting it is lossless, and carrying it only inflates context (Failure 8).*
4. **Installation is a join, not an overwrite.** *Let $p_{\text{old}}$ be an installed package, for example one that has accumulated forged scripts, and let $p_{\text{new}}$ be a recomposition. Overwriting is an upgrade in $\sqsubseteq$ iff $C_{p_{\text{old}}} \setminus C_{p_{\text{new}}} = \emptyset$. Otherwise the least package that dominates both is the join $p_{\text{old}} \sqcup p_{\text{new}}$, whose carrier is $C_{p_{\text{old}}} \cup C_{p_{\text{new}}}$ when they agree on shared paths. It satisfies $I(Y^*; M, E_{\sqcup}) \ge \max\big(I(Y^*; M, E_{\text{old}}),\, I(Y^*; M, E_{\text{new}})\big)$.*

*Proof.* (1) Under reference locality, $K_i$ depends on its carrier only through $\operatorname{cl}(s_i)$. A byte-identical relocation with rewritten references gives the agent the same reachable files and the same execution results, so the kernels agree. Theorem 3.1 supplies the theory half.

(2) This is the chain rule for mutual information applied to the observation tuple $(M, E_C)$: removing $E_f$ subtracts exactly the conditional term, and conditional mutual information is non-negative.

(3) Immediate from reference locality.

(4) $\sqsubseteq$ is inclusion of finite sets, so $p_{\text{new}}$ dominates $p_{\text{old}}$ iff nothing in $C_{p_{\text{old}}}$ is absent from $C_{p_{\text{new}}}$. The least upper bound of two sets that agree on shared paths is their union. The information bound follows from $I(Y^*; A, B) \ge I(Y^*; A)$. $\square$

**Implementation.** `compose_skills.py` computes $\operatorname{cl}(s_i)$ by scanning each member `SKILL.md` and the files it reaches, within the member's repository and to bounded depth. It copies the closure to `scripts/members/<slug>/` and `references/members/<slug>/`, with out-of-folder files placed under `_repo/`, and records source path, destination, and SHA-256 under `carrier` in `manifold_atlas.json`. `install_skill_dual.sh` checks part 4 before it touches any destination. When $C_{\text{old}} \setminus C_{\text{new}} \neq \emptyset$, it exits 2 with `install_would_lose_files` and the lost paths, so the caller forms the join. `--allow-loss` is an explicit opt-out.

A package's install name is its identity: part 4 joins packages that share one. `--new-skill-name` asks for a fresh identity instead, so $p_{\text{old}}$ is the empty package and the join is $p_{\text{new}}$ itself, with no earlier skill touched. `parse_args.py` refuses a name already installed on any host, and the installer's `--new` mode re-checks at install time, so a composition meant to be new cannot silently become an update of an older skill.

---

## 4. Software Engineering Kleisli Composition & Agentic Control Laws

Each module inside the manifold-parameterized workflow remains an **Open Effectful Kleisli Transducer** $\mathcal{S} = \langle I, O, P, Q, \mathcal{F}, \mathcal{E}, \mathcal{B} \rangle$ wired via **six algebraic operators** checked by `scripts/wiring_compiler.py`:

1. **Lawvere–Amari Chart Projection ($\sigma^* : \mathcal{X} \to \Theta$):** Projects raw input onto contradiction-free fiber coordinates $\theta^*(x)$ and halts with exit-`2` `ABSTAIN_OFF_MANIFOLD` outside the conormal domain guard.
2. **Sequential Kleisli Pipe ($S_2 \circ_\alpha S_1$):** Enforces Meyer Hoare refinement $Q_1(x, y_1) \implies P_2(\alpha(y_1))$ and Benveniste–Henzinger contract consistency via minimal sufficient-statistic adapters $\alpha$.
3. **Parallel Tensor ($S_1 \otimes S_2$):** Enforces Concurrent Separation Logic frame disjointness $\mathcal{W}_1 \cap (\mathcal{W}_2 \cup \mathcal{R}_2) = \emptyset$ and $\mathcal{W}_2 \cap \mathcal{R}_1 = \emptyset$.
4. **Guarded Coproduct ($G \triangleright (S_1 \oplus S_2 \oplus \texttt{ABSTAIN})$):** Total routing with Liskov Behavioral Subtyping.
5. **Sheaf Equalizer / Pullback Join ($\Gamma(\mathcal{U}, \mathcal{F}) = \ker \delta^0$):** Enforces $\delta^1 = 0$ statically and $\pi_K(O_u) = \pi_K(O_v)$ dynamically across overlapping artifact views.
6. **Post-Dominator Orthogonal Feedback Loop ($\mu X.\; \text{Gate}_Q \circ (S_{\text{act}} \leftrightarrows S_{\text{crit}})$):** Every mutator node $m \in V_{\text{mut}}$ is post-dominated on all paths to `DONE` by a read-only exogenous gate ($\mathcal{W}(g) = \emptyset$, SHA-256 verified) governed by a DAG-ordered **Lyapunov potential** $\Phi(x_t)$ and **Conditional Lempel–Ziv MDL** anti-padding (`info_density >= 0.10`).

### 4.1 A contract calculus over prose and script components

The six operators form a typed term language whose components are of two kinds: prose $\langle\pi\rangle$, interpreted by the model, and scripts $\llbracket f\rrbracket$, run by the host.

$$c ::= \langle\pi\rangle \mid \llbracket f\rrbracket \qquad s ::= c \mid s\,;_\alpha s \mid s \otimes s \mid g \triangleright (s \oplus s \oplus \texttt{ABSTAIN}) \mid \text{glue}_{\mathcal{U}}(s_u) \mid \text{gate}_G(s) \mid \text{proj}_{\mathcal{M}} \triangleright s$$

Every component has an interface $\iota(c) = (\mathcal{A}_c, R_c, W_c, E_c, \nu_c)$: argument signature, read and write footprints, exit statuses, and a **total** verdict map $\nu_c : \mathbb{Z} \to \{\text{pass}, \text{abstain}, \text{fail}\}$ with $\nu_c(e) = \text{fail}$ outside $E_c$. For scripts, $\mathcal{A}_f$ and $E_f$ come from `script_signature` (argument-parser declarations and exit literals in the Python AST, including the `SystemExit(main())` idiom) and are recorded under `script_interfaces` in `manifold_atlas.json`. Verdict maps are per component: the projector reads exit 2 as abstain, the gate reads exit 2 as fail, and a foreign member script reads every nonzero status as fail, since 2 is argparse's usage error. Prose has $E = \{0\}$ and never reports a verdict, so its correctness must be discharged by a later script.

Sequential verdicts short-circuit ($v_1 \triangleright v_2 = v_1$ unless $v_1 = \text{pass}$), a monoid with abstain and fail as left zeros; parallel verdicts take the meet in $\text{fail} < \text{abstain} < \text{pass}$. Typing rules (T-Prose, T-Script, T-Seq, T-Par, T-Guard, T-Glue, T-Gate, T-Proj) mark each premise as static (wiring verifier), dynamic (generated monitor), or assumed (prose entailment $Q_1 \Rightarrow \alpha^* P_2$, which is undecidable here).

**Threat model.** The model is an adversary at prose positions. The trusted base is: (T1) scripts and monitors run as coded; (T2) the host runs the projector before any prose step and admits `DONE` only immediately after a passing gate; (T3) SHA-256 collision resistance. Today's hosts state T2 in the skill text but do not enforce it.

**Soundness.** Under T1 to T3, every trace of $\text{proj}_{\mathcal{M}} \triangleright \text{gate}_G(s)$ satisfies the LTL safety properties

- $\varphi_{\text{abs}} = (\neg\text{wr}\ \mathbf{U}\ \text{ex(proj)}) \land \mathbf{G}(\text{ex(proj},2) \to \mathbf{G}\neg\text{wr})$ (the projector's own `--out` report is its declared write),
- $\varphi_{\text{gate}} = \mathbf{G}(\text{wr} \to \neg\text{done}\ \mathbf{W}\ \text{ex(gate},0))$,
- $\varphi_{\text{ro}} = \mathbf{G}(\text{ex(gate},0) \to H_{\text{pre}}(W) = H_{\text{post}}(W))$,
- $\varphi_{\text{glue}} = \mathbf{G}(\text{done} \to \delta^0 y = 0)$,

whatever the model does. Each is an Alpern–Schneider safety property, so a monitor can enforce it (Schneider's security automata); the projector, gate, and installer are those monitors. The static dominance checks (gate post-dominates every mutator, and projector pre-dominates every mutator, both in `dominator_orthogonality`) give conformance: an agent that follows the compiled graph cannot reach a state whose only continuation violates a property. `DONE` certifies only the gate's checks.

---

## 5. Mapping Theory to Executable `/skillcompose` Scripts & Proof Suites

| Theoretical Mechanism | Executable Implementation | Reproducible Verification Suite |
|---|---|---|
| Guarded Markov kernels over 648 structured outputs, Conditional Fisher–Rao metric $G_F$, Galois conormal core, Plotkin–Reynolds anti-unification $\sqcup_{\text{lgg}}$, Čech cocycle checker | `scripts/manifold_engine.py` | `metrics/manifold-lift/measure.py` |
| Query-conditioned submodular Noisy-OR $p(u \mid s, Q)$ + Log-Det Fisher volume $V_{\text{Fisher}}(S)$ + JSD/NCD anti-redundancy + exemplar conflict penalty + Nemhauser–Wolsey certificate | `scripts/submodular_select.py` | `metrics/principled-lift/measure.py`, `metrics/manifold-lift/measure.py` |
| 6-operator Kleisli + Sheaf wiring compiler & 6-theorem static verifier (`type_safety`, `separation_logic`, `dpi_exogenous_grounding`, `dominator_orthogonality`, `parnas_encapsulation`, `manifold_sheaf_exactness`) | `scripts/wiring_compiler.py` | `metrics/principled-lift/measure.py`, `metrics/manifold-lift/measure.py` |
| Composed argument interface $\mathcal{A}_{\mathcal{M}}(D)$: arguments the final skill takes ($T_\cap \cup D_{\text{take}}$) and is able to take ($B_\cup \cup D_{\text{able}}$); empty $D$ is anti-unification of member signatures | `scripts/parse_args.py` (`--args` → `desired_interface`) | Corollary 3.1; `/skillcompose … --args "--author-persona, take:--premise"` |
| Hybrid contract calculus: script signatures $\operatorname{sig}(f)$, per-component verdict maps, projector pre-dominance, LTL safety under T1–T3 (§4.1) | `scripts/compose_skills.py` (`script_interfaces`), `scripts/wiring_compiler.py` (`dominator_orthogonality`) | `metrics/carrier-closure/measure.py` (`check_signatures`), `paper/main.tex` Theorem 5 |
| Carrier closure $\operatorname{cl}(s_i)$ of member channels and modules (kernel-exact pullback) and installation as join in $\sqsubseteq$ (Proposition 3.2) | `scripts/compose_skills.py` (`carrier` in `manifold_atlas.json`), `scripts/install_skill_dual.sh` (`install_would_lose_files`) | `metrics/carrier-closure/measure.py` |
| End-to-end composite manifold compiler emitting `MANIFOLD_ATLAS.md`, standalone `project_manifold.py`, & sheaf/SHA-256 `verify_dominator_gate.py` (+ 4-platform manifests) | `scripts/compose_skills.py`, `scripts/export_platform_targets.py` | `metrics/manifold-lift/measure.py`, `metrics/principled-lift/measure.py` |
| Conditional DEFLATE/LZ novelty, Attention Channel SNR, & Lyapunov debt $\Phi$ | `scripts/information_gain.py` | `metrics/principled-lift/measure.py` |
