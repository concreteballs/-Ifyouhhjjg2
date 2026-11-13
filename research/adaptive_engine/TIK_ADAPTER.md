# Adaptive TIK adapter

This adapter connects the adaptive search to the actual existing calculation chain:

`ModelInputs -> calculate_local_state -> calculate_return_flow -> paired contrast -> response fitting`.

For every paired observation, both local states are calculated by the canonical TIK-0 and return-flow modules. The adapter searches over:
- return-flow family (`linear`, `power`, `saturating`);
- return coefficient;
- power exponent where applicable;
- downstream response family and its fitted parameters.

The paired input feature is the returned-power-density difference divided by the mean incoming power density of the pair. This is a numerical normalization for stable fitting; it is not a physical assertion.

The selected result includes both the return-flow settings and downstream response candidate, plus a stability report. Candidates that fail the configured local stability test are strongly penalized and remain visible among alternatives.

## Scope

- This is now an end-to-end fit over actual TIK local-state inputs, rather than fitting a detached abstract curve only.
- It does not yet automatically optimize the raw geometric TIK inputs (cell count, cell volume, observation volume, transmission probability, event energy, channel coverage, probability and efficiency). Those remain supplied inputs; adding constrained search over selected inputs is the next extension.
- It searches declared formula families, not arbitrary symbolic expressions.
- The output is a fitted configuration for the supplied observations. Use separate datasets or perturbation tests to assess generalization.

## Applicability-aware dataset orchestration

The higher-level `fit_tik_research_dataset` wrapper accepts `TIKResearchObservation` records that pair each existing `TIKPairObservation` with a process profile and provenance group.

It calls the process applicability engine before fitting. Only `FIT` records reach `fit_tik_pairs`. `PARTIAL_TRANSFER` records are retained and reported separately. `HOLDOUT` records are evaluated only after fitting, using the selected return-flow settings and response formula with frozen parameters; holdout values are never sent back into the optimizer.

The result includes the fitted model, all applicability roles, holdout predictions and errors, and explicit ID lists for fit, holdout, partial transfer, adaptation, excluded and unresolved observations.
