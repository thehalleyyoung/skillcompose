# Algebraic & Manifold Wiring Contract — `ml-paper-manifold`

Synthesized via Lawvere–Amari Manifold Chart Projection, Kleisli Design-by-Contract, Concurrent Separation Logic, Čech Sheaf Gluing, DPI Exogenous Grounding, and Post-Dominator Orthogonal Verification.

## Operators & Typed Frames

| Operator ID | Class | Inputs | Outputs | Writes (Frame) | Exogenous Oracle |
|---|---|---|---|---|---|
| `subskill:intent-guard-router` | `guard_router` | `raw_user_request` | `task_request`, `workspace_context` | ∅ *(read-only)* | yes |
| `subskill:manifold-chart-projector` | `manifold_projector` | `task_request`, `workspace_context` | `manifold_fiber_section`, `task_request`, `workspace_context` | `spec/manifold_section.json` | yes |
| `member:latex-fmt` | `specifier` | `task_request`, `workspace_context` | `locked_spec_packet` | `spec/locked_spec.json` | no |
| `member:anti-defensive-writing` | `mutator` | `locked_spec_packet` | `candidate_artifact` | `workspace_artifacts:slice_1` | no |
| `member:conference-paper-writing` | `mutator` | `locked_spec_packet` | `candidate_artifact` | `workspace_artifacts:slice_2` | no |
| `member:research-paper-writing` | `mutator` | `locked_spec_packet` | `candidate_artifact` | `workspace_artifacts:slice_3` | no |
| `member:paper-writing-skill` | `mutator` | `locked_spec_packet` | `candidate_artifact` | `workspace_artifacts:slice_4` | no |
| `subskill:pullback-claim-provenance-table` | `pullback_join` | `locked_spec_packet`, `candidate_artifact` | `reconciled_artifact_bundle`, `pullback_witness` | `review/pullback_claim_ledger.json` | yes |
| `member:citation-verifier` | `readonly_critic` | `reconciled_artifact_bundle`, `locked_spec_packet` | `static_contract_report` | ∅ *(read-only)* | yes |
| `member:citation-management` | `readonly_critic` | `reconciled_artifact_bundle`, `locked_spec_packet` | `static_contract_report` | ∅ *(read-only)* | yes |
| `member:peer-review` | `readonly_critic` | `reconciled_artifact_bundle`, `locked_spec_packet` | `adversarial_critique_report` | ∅ *(read-only)* | no |
| `oracle:exogenous-env-runner` | `exec_observation` | `reconciled_artifact_bundle`, `locked_spec_packet` | `empirical_execution_trace` | ∅ *(read-only)* | yes |
| `subskill:verify-gate` | `oracle_gate` | `reconciled_artifact_bundle`, `pullback_witness`, `empirical_execution_trace` | `verified_certificate_or_lyapunov_repair_card` | ∅ *(read-only)* | yes |

## Lawvere–Amari Generative Manifold Summary

- **Riemannian Tangent Rank ($\dim T\mathcal{M}$):** `6` (intrinsic dimension $d_{\text{eff}} = 4.4743$)
- **D-Optimal Fisher Log-Det Volume:** `6.5515`
- **Structured Output Fiber Expansion:** union `32` $\to$ manifold `72` (`+40` recombinant states)
- **Anti-Unified Chart Variables ($\Theta$):** `spec_modality`, `execution_regime`, `verification_channel`, `failure_semantics`, `gluing_topology`

## Sheaf Gluing & Pullback Invariant (`Γ(U, F) = ker δ^0`)

- **Primary Pullback Key (`K`):** `claim_provenance_table` (`review/pullback_claim_ledger.json`)
- **Commutative Invariant:** `every quantitative claim cites source_id + exact numerator/denominator check`
- **Sheaf Open Cover (`U`):** `U_claim_protocol`, `U_evidence_table`, `U_stat_computation`, `U_citation_audit`

## Static Verification Summary

- **type_safety**: `PASS`
- **separation_logic**: `PASS`
- **dpi_exogenous_grounding**: `PASS`
- **dominator_orthogonality**: `PASS`
- **parnas_encapsulation**: `PASS`
- **manifold_sheaf_exactness**: `PASS`
