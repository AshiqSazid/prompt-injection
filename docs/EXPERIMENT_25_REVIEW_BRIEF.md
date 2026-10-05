# Experiment 25: independent review brief

Prepared 2026-09-29. This is a request for review, not evidence of completed
independent review. No model observations have been collected in either stage.

Read `JOURNAL_EXTENSION_PROTOCOL.md`, `EXPERIMENT_25_MOTIVATION.md`,
`code/schema_types_design.py`, `code/schema_types_analyze.py` and
`data/extension_design.json` together. The prior larger four-task/defense
proposal is superseded for this collection, not silently retained in the budget.

Please resolve these questions before sealing:

1. **Estimand and pairing.** Does the A contrast isolate the canary-permitting
   pattern/length manipulation? It averages the free-minus-constrained received
   target outcome over four fixed naming fields. Replicates share canaries across
   fields, and uncertainty resamples complete replicate blocks. Provider sampling
   seeds are not guaranteed paired random draws.
2. **Precision.** Is twenty blocks adequate for the effect size the authors care
   about? The 20-replicate, 20-pp scenarios with independent paired draws give
   only about 78–79% single-provider interval-exclusion frequency under the
   stated simulation assumptions; that does not establish 80% joint power.
   Some conditional coverage estimates are below 95%. Check simulations and
   dependence assumptions, rather than approving a threshold by name.
3. **Small fixed design.** Four fields are purposive and one tool is synthetic.
   Conditional block intervals and field-composition sensitivities must not be
   sold as coverage over arbitrary schemas, tasks or deployments.
4. **Capacity.** Enum and integer have eight categories, boolean has two.
   Domain wording differs, so cross-domain rates are not pure type comparisons.
   Review balanced hidden-label controls, within-schema label permutations,
   handling of no-calls and six-test Holm correction.
5. **Endpoints.** The host validates before local handler receipt. Lower received
   recovery may include schema rejection, not changed intent. Review emission,
   redirection, API-error bounds and legitimate-task utility together. Local
   handler receipt is not MCP transport or a real provider receipt.
6. **Conditional B.** B is one fixed naming field, eight native contexts and five
   pairs per provider/context. Funding must be independent of observed A results.
   It is a small contextual check; it cannot rescue A or establish four-family
   generalization. Confirm the one-field choice before observation.
7. **Pre-collection integrity.** Review exact model/schema compatibility, source
   licenses, fixture correctness, token bounds, durable budget/checkpoint behavior,
   freeze hashes and witness verification. Token accounting, the durable
   pre-attempt budget journal and resume were implemented on 2026-09-29; review
   the bounds and the resume policy in the protocol's cost section.

Record reviewer identity, date, comments, required amendments and their resolution.
Do not mark `statistical_review` confirmed merely because regression tests pass.
Changes before sealing are permissible and should update the protocol, code,
planner, tests and hashes together. Changes after observation need transparent
amendment/deviation status; they cannot be retroactively preregistered.
