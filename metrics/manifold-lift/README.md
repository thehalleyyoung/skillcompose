# `manifold-lift` — Lawvere–Amari Generative Skill Manifold Proof Suite

Offline verification suite proving that `/skillcompose` synthesizes a **parameterized generative transducer over structured outputs** ($\mathfrak{G}_{\mathcal{M}} : x \mapsto K_{\theta^*(x)}(\cdot \mid x)$ supported on $\mathcal{Y}_{\mathcal{T}_{\mathcal{M}}(\theta^*(x))}(x)$) that strictly dominates both **prompt concatenation** ($\bigwedge_i Q_i$) and **skill union / routing** ($\bigcup_i s_i$, $\frac{1}{N}\sum_i K_i$).

## Verified Theorems & Runtime Gates

1. **`fisher_logdet_exact_submodularity`**: Exhaustively verifies exact monotone submodularity (diminishing returns) of D-optimal Fisher Log-Determinant Spanning Volume $V_{\text{Fisher}}(S) = \frac{1}{2}\log\det(I_D + \alpha \tilde{\Psi}_S^\top \tilde{\Psi}_S)$ across combinatorial subset pairs $S \subset T$.
2. **`galois_anti_unification_defeats_concatenation_collapse`**: Verifies that when observed skills specialize conflicting operational regimes, conjunction $\bigwedge_i Q_i$ collapses to an empty output fiber ($|\mathcal{Y}_{\cap}| = 0$), whereas Galois conormal extraction + Plotkin–Reynolds anti-unification ($\sqcup_{\text{lgg}}$) expands the admissible structured output fiber while preserving exact pullback recovery $\sigma_i^* \mathcal{T}_{\mathcal{M}} \equiv Q_i \land \Phi_{\text{core}}$.
3. **`recombinant_out_of_sample_beats_union_and_router`**: On unseen recombinant coordinates $\theta^* \notin \{\theta^{(1)}, \dots, \theta^{(N)}\}$, proves that both union/mixture and nearest-neighbor routing assign zero probability mass ($D_{\text{KL}} = +\infty$), while Lawvere–Amari chart projection achieves full fiber support and $<0.01$ bits KL divergence.
4. **`amari_e_geodesic_strictly_diverges_from_m_mixture`**: Verifies Amari's $e$-geodesic vs $m$-mixture Bregman divergence gap on the conditional statistical manifold over structured outputs.
5. **`wiring_rejects_unlifted_collision_and_holonomy_cocycle_defect`**: Verifies static Theorem 6 (`manifold_sheaf_exactness`) catches unparameterized constraint collisions and non-zero Čech 1-cocycle triangle holonomy ($\delta^1 \neq \mathrm{id}$).
6. **`compiled_package_projector_and_sheaf_coboundary_gate`**: Executes synthesized `project_manifold.py` (in-manifold chart projection + `ABSTAIN_OFF_MANIFOLD` exit `2`) and `verify_dominator_gate.py --glue` (Čech 0-coboundary check $\delta^0(y) = 0$).

## Run

```bash
python3 metrics/manifold-lift/measure.py
```
