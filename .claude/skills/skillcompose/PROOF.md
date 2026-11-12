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
| `outcome-contract` (`no_evidence_refused`, `unchanged_output_refused`, `invented_excerpt_refused`, `real_improvement_passes`, `outputs_not_product_chars`, `self_measurement_flagged`, `append_without_outcome_refused`, `drift_forge_fails`, `flat_output_fails`, `evidence_free_forge_fails`) | From round 11, a forge round must show the composed skill's output before and after its change, with the named flaw quoted from the output; a forge where more than 20% of rounds are mostly evals/metrics/tests, or where the output improved in fewer than half, fails validation. |
| `adversarial-args` / `remix-coherence` / `propose-audits-gate` / `local-only-cache` / `status-pack-bytes` / `dry-run-protect` / `smoke-refusal-suite` | Full backward-compatible CLI refusal safety (exit code `2`), offline cache determinism, compact status telemetry, and full-mode dry-run stamp protection. |

## Why the outcome contract exists

A 50-round `/skillcompose` forge of a fantasy-writing skill (eight members, `fantasy-draft`) passed every earlier gate, and `outcome_round.py audit` shows where its effort went. Across rounds 11–50, 672,898 changed characters went to evals, metrics, gold labels and METRICS.md, 293,837 to the skill itself, and 108,258 to the novella it wrote. 25 of those 40 rounds spent most of their change measuring the package (nearly all of rounds 21–44). No round recorded what the skill wrote for a user before and after its change. Each round found a gap in the package's own instruments and closed it, so the forge improved skillcompose's view of the skill more than the fiction the skill produces. Under the outcome contract, `ship_check.py` refuses that forge with two reasons: rounds without before/after output evidence, and self-measurement drift (23 of 40 rounds by the fork's own output folders).

## Reproducible Verification Commands

```bash
bash scripts/dry_run_gates.sh
python3 metrics/manifold-lift/measure.py
python3 metrics/principled-lift/measure.py
python3 metrics/outcome-contract/measure.py
```

All 10 gate suites must exit `0` and stamp `review/last_dry_run.json` with `"mode": "full", "pass": true`.
