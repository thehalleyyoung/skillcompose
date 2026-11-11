# `skillcompose` — Proof & Gate Verification Card

## Core Verified Capabilities

| Gate / Invariant | What It Proves |
|---|---|
| `manifold-lift` (`fisher_logdet_exact_submodularity`) | D-optimal Fisher Log-Determinant Spanning Volume $V_{\text{Fisher}}(S) = \frac{1}{2}\log\det(I_D + \alpha \tilde{\Psi}_S^\top \tilde{\Psi}_S)$ satisfies exact monotone submodularity (diminishing returns) across subset pairs $S \subset T$. |
| `manifold-lift` (`galois_anti_unification_defeats_concatenation_collapse`) | Galois conormal extraction ($\Phi_{\text{core}}$) + Plotkin–Reynolds anti-unification ($\sqcup_{\text{lgg}}$) lifts conflicting clauses ($|\mathcal{Y}_{\bigwedge Q_i}| = 0$) into Lawvere chart variables $\theta \in \Theta$ while preserving exact landmark specialization $\sigma_i^* \mathcal{T}_{\mathcal{M}} \equiv Q_i \land \Phi_{\text{core}}$. |
| `manifold-lift` (`recombinant_out_of_sample_beats_union_and_router`) | On unseen recombinant chart coordinates $\theta^* \notin \{\theta^{(1)}, \dots, \theta^{(N)}\}$, both union/mixture ($\sum_i w_i K_i$) and single-skill routing assign $0$ probability mass ($D_{\text{KL}} = +\infty$), while Lawvere–Amari manifold projection achieves full fiber support and $<0.01$ bits KL divergence. |
| `manifold-lift` (`amari_e_geodesic_strictly_diverges_from_m_mixture`) | Exponential ($e$-)geodesic KL barycenter on the conditional statistical manifold exhibits strictly positive Bregman divergence gap over linear $m$-mixtures. |
| `manifold-lift` (`wiring_rejects_unlifted_collision_and_holonomy_cocycle_defect`) | Static Theorem 6 (`manifold_sheaf_exactness`) rejects unparameterized clause collisions and non-zero Čech 1-cocycle triangle holonomy ($\delta^1 \neq \mathrm{id}$). |
| `manifold-lift` (`compiled_package_projector_and_sheaf_coboundary_gate`) | Compiled `project_manifold.py` projects valid tasks (`exit 0`), refuses off-manifold polysemy (`exit 2`), and `verify_dominator_gate.py --glue` enforces Čech 0-coboundary agreement ($\delta^0(y) = 0$). |
| `principled-lift` (`submodular_beats_github_top_n`, `wiring_compiler_sound`, `reject_gate_bypass_shortcut`, `reject_parallel_write_race`, `mdl_catches_padding_passes_code`, `compose_and_dominator_gate_enforces_separation_logic`) | Submodular + Fisher-volume + JSD/NCD selection beats GitHub Popularity-Top-N with Nemhauser–Wolsey certificate; Separation Logic, Post-Dominator SHA-256 non-mutation, and DEFLATE/LZ anti-padding hold. |
| `adversarial-args` / `remix-coherence` / `propose-audits-gate` / `local-only-cache` / `status-pack-bytes` / `dry-run-protect` / `smoke-refusal-suite` | Full backward-compatible CLI refusal safety (exit code `2`), offline cache determinism, compact status telemetry, and full-mode dry-run stamp protection. |

## Reproducible Verification Commands

```bash
bash scripts/dry_run_gates.sh
python3 metrics/manifold-lift/measure.py
python3 metrics/principled-lift/measure.py
```

All 9 gate suites must exit `0` and stamp `review/last_dry_run.json` with `"mode": "full", "pass": true`.
