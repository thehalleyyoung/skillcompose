# Lawvere–Amari Generative Skill Manifold Atlas — `ml-paper-manifold`

This skill is **not** a prompt concatenation ($\bigwedge_i Q_i$, which collapses on conflicting regimes) nor a mere router/union ($\bigcup_i s_i$, which cannot synthesize off-sample combinations). It compiles the observed member skills as landmark sections of a **Conditional Statistical–Logical Manifold** $\mathfrak{G}_{\mathcal{M}} = \langle \Theta, \mathcal{T}_{\mathcal{M}}, g_F, \mathcal{N}(\mathcal{U}) \rangle$ mapping each task input $x \in \mathcal{X}$ to a constrained fiber of structured outputs $\mathcal{Y}_{\mathcal{M}}(x)$.

## 1. Information-Geometric Summary (Amari Conditional Fisher–Rao Metric)

- **Structured Output Lattice Cardinality ($|\mathcal{Y}|$):** `648`
- **Riemannian Tangent Rank ($\dim T_{\bar{\eta}_0}\mathcal{M}$):** `6`
- **Effective Intrinsic Dimension (Participation Ratio $d_{\text{eff}}$):** `4.4743`
- **D-Optimal Fisher Log-Det Spanning Volume ($V_{\text{Fisher}}(S)$):** `6.5515`
- **Amari $e$-Geodesic vs $m$-Mixture Bregman Gain:** `0.07344 bits`

## 2. Logical Normal–Tangent Decomposition (Galois Closure + Anti-Unification)

- **Concatenation Admissible Fiber ($|\mathcal{Y}_{\bigwedge Q_i}|$):** `0` (conflicts lifted: `6`)
- **Point-Union Admissible Fiber ($|\bigcup_i \mathcal{Y}_i|$):** `32`
- **Manifold Total Admissible Fiber ($|\mathcal{Y}_{\mathcal{T}_{\mathcal{M}}(\Theta)}|$):** `72` (`+40` recombinant structured output states)
- **Exact Landmark Specialization ($\forall i,\; \sigma_i^* \mathcal{T}_{\mathcal{M}} \equiv Q_i \land \Phi_{\text{core}}$):** `True`

### Conormal Universal Invariants ($N^*\mathcal{M} = 0$, Always Enforced)

- **`spec_modality`** $\in \{`formal_grammar_adr`, `informal_prose`, `json_contract`\}$
- **`execution_regime`** $\in \{`single_shot`, `streaming_incremental`, `transactional_staged`\}$
- **`verification_channel`** $\in \{`adversarial_differential`, `exogenous_exec_oracle`, `static_ast_contract`\}$
- **`failure_semantics`** $\in \{`abstain_exit2`, `idempotent_rollback`\}$
- **`gluing_topology`** $\in \{`pairwise_handoff`, `sheaf_global_section`\}$
- **`context_disclosure`** $\in \{`progressive_parnas`\}$

### Anti-Unified Tangent Chart Coordinates ($\theta \in \Theta$)

- **`theta_spec_modality`** (`spec_modality`): domain $\{`formal_grammar_adr`, `informal_prose`, `json_contract`\}$
- **`theta_execution_regime`** (`execution_regime`): domain $\{`single_shot`, `transactional_staged`\}$
- **`theta_verification_channel`** (`verification_channel`): domain $\{`adversarial_differential`, `exogenous_exec_oracle`, `static_ast_contract`\}$
- **`theta_failure_semantics`** (`failure_semantics`): domain $\{`abstain_exit2`, `idempotent_rollback`\}$
- **`theta_gluing_topology`** (`gluing_topology`): domain $\{`pairwise_handoff`, `sheaf_global_section`\}$

## 3. Landmark Anchors on $\mathcal{M}$

| Landmark | Upstream ID | Fisher Tangent Coordinates $\theta^{(i)}$ | Specialized Fiber Clauses |
|---|---|---|---|
| `latex-fmt` | `Calix-L/awesome-latex-skills@latex-fmt` | `[+0.30, +1.05, +0.78, -0.28, -0.47, +0.02]` | `spec_modality=['formal_grammar_adr', 'informal_prose', 'json_contract']; execution_regime=['single_shot']; verification_channel=['static_ast_contract']; failure_semantics=['abstain_exit2', 'idempotent_rollback']; gluing_topology=['pairwise_handoff']` |
| `citation-verifier` | `Boom5426/Nature-Paper-Skills@citation-verifier` | `[-0.73, -0.23, +0.15, -0.32, -0.23, -0.40]` | `spec_modality=['formal_grammar_adr', 'informal_prose', 'json_contract']; execution_regime=['single_shot']; verification_channel=['static_ast_contract']; failure_semantics=['abstain_exit2', 'idempotent_rollback']; gluing_topology=['sheaf_global_section']` |
| `citation-management` | `K-Dense-AI/scientific-agent-skills@citation-management` | `[+0.59, +0.28, -0.72, -0.82, +0.47, -0.11]` | `spec_modality=['json_contract']; execution_regime=['transactional_staged']; verification_channel=['static_ast_contract']; failure_semantics=['abstain_exit2', 'idempotent_rollback']; gluing_topology=['pairwise_handoff', 'sheaf_global_section']` |
| `anti-defensive-writing` | `Boom5426/Nature-Paper-Skills@anti-defensive-writing` | `[+1.43, -0.00, -0.29, +0.74, -0.13, -0.07]` | `spec_modality=['json_contract']; execution_regime=['transactional_staged']; verification_channel=['adversarial_differential']; failure_semantics=['idempotent_rollback']; gluing_topology=['pairwise_handoff']` |
| `conference-paper-writing` | `Boom5426/Nature-Paper-Skills@conference-paper-writing` | `[+0.18, -0.65, +0.86, -0.26, +0.31, +0.36]` | `spec_modality=['formal_grammar_adr', 'informal_prose', 'json_contract']; execution_regime=['single_shot']; verification_channel=['exogenous_exec_oracle', 'static_ast_contract']; failure_semantics=['idempotent_rollback']; gluing_topology=['pairwise_handoff', 'sheaf_global_section']` |
| `research-paper-writing` | `Master-cai/Research-Paper-Writing-Skills@research-paper-writing` | `[-0.18, -1.24, +0.14, +0.27, -0.04, -0.16]` | `spec_modality=['formal_grammar_adr', 'informal_prose', 'json_contract']; execution_regime=['single_shot']; verification_channel=['adversarial_differential', 'exogenous_exec_oracle', 'static_ast_contract']; failure_semantics=['idempotent_rollback']; gluing_topology=['sheaf_global_section']` |
| `paper-writing-skill` | `SNL-UCSB/paper-writing-skill@paper-writing-skill` | `[-0.92, +0.87, +0.07, +0.70, +0.50, -0.02]` | `spec_modality=['formal_grammar_adr']; execution_regime=['transactional_staged']; verification_channel=['exogenous_exec_oracle', 'static_ast_contract']; failure_semantics=['abstain_exit2']; gluing_topology=['pairwise_handoff', 'sheaf_global_section']` |
| `peer-review` | `K-Dense-AI/scientific-agent-skills@peer-review` | `[-0.67, -0.08, -0.98, -0.03, -0.41, +0.36]` | `spec_modality=['json_contract']; execution_regime=['single_shot']; verification_channel=['adversarial_differential', 'exogenous_exec_oracle', 'static_ast_contract']; failure_semantics=['abstain_exit2']; gluing_topology=['sheaf_global_section']` |

## 4. Sheaf Gluing Nerve $\mathcal{N}(\mathcal{U})$ ($\Gamma(\mathcal{U}, \mathcal{F}) = \ker \delta^0$)

- **Open Cover ($\mathcal{U}$):** `U_claim_protocol`, `U_evidence_table`, `U_stat_computation`, `U_citation_audit`
- **Čech 1-Cocycle Exactness ($\delta^1 = 0$):** `PASS` (`1` triangles verified)
- **Restriction `U_claim_protocol ∩ U_evidence_table`**: must agree on keys `['claim_ids', 'denominators']` (`transform=id`)
- **Restriction `U_evidence_table ∩ U_stat_computation`**: must agree on keys `['claim_ids', 'denominators']` (`transform=id`)
- **Restriction `U_claim_protocol ∩ U_stat_computation`**: must agree on keys `['claim_ids', 'denominators']` (`transform=id`)
- **Restriction `U_evidence_table ∩ U_citation_audit`**: must agree on keys `['source_hashes']` (`transform=id`)
