# Applicability-aware TIK research pipeline

## Purpose

This module connects the process analogy/applicability engine to the existing paired TIK-0 adaptive adapter. It turns classification into an enforceable data-flow rule rather than a descriptive label.

## Input

Each `TIKResearchObservation` contains:
- a `TIKPairObservation` with the two TIK local-state inputs and observed output delta;
- a provenance `group_id` (experiment, source run, object lineage or another leakage boundary);
- a `ProcessProfile` describing process family, structure, function, operating conditions, I/O variables, ranges, capabilities and provenance.

The caller supplies a reference profile and explicit fit/holdout group IDs.

## Processing sequence

1. `build_applicability_split` classifies all observations.
2. Only `FIT` observations are passed to `fit_tik_pairs`.
3. `PARTIAL_TRANSFER` and `ADAPTATION_REQUIRED` observations are retained in separate result lists; they are not silently mixed into direct model fitting.
4. Holdout candidates must be compatible with the target model and have provenance independent of the complete fit population.
5. The selected fit is frozen. Holdout features are calculated through the same canonical TIK-0/return-flow chain and passed through the selected response formula without optimization or parameter changes.
6. Per-observation predictions and absolute errors, RMSE and weighted RMSE are returned.

## Result

`TIKResearchResult` contains:
- the fitted `TIKAdaptiveResult`;
- all `ObservationRole` classifications and rationales;
- fit and holdout observation IDs;
- partial-transfer, adaptation-required, excluded and unresolved IDs;
- an optional `TIKHoldoutReport` with frozen predictions and error metrics.

## Guardrails

- At least two eligible FIT observations are required.
- FIT and HOLDOUT groups must be disjoint.
- A shared source or experiment lineage with any fit observation prevents holdout promotion.
- Missing provenance is not treated as evidence of independence.
- Partial analogues are not scored as direct validation.
- Holdout observations never enter `fit_tik_pairs`.

This pipeline does not yet automatically synthesize new TIK input parameters from partial analogues. It establishes the safe orchestration boundary and preserves the partial-transfer material for a subsequent component-level adaptation/search layer.

## Component transfer and candidate recombination

The component transfer search consumes only observations already classified as
`PARTIAL_TRANSFER`. A caller must declare explicit mapping rules; no implicit
parameter copying occurs. Each rule maps one shared capability to a raw TIK
parameter and may define multiple multiplier/offset transformations. Hints
from different analogue processes are merged by target parameter and side,
then expanded into deterministic, deduplicated candidate combinations under
a hard candidate-count limit.

The search runs each combination through the raw-parameter fitter using only
the original `FIT` observation IDs. It does not refit on `HOLDOUT`; it evaluates
the frozen candidate and ranks candidates by holdout weighted RMSE when an
independent holdout exists. Without holdout data, ranking falls back to the
fit score and is explicitly exploratory. Proposal IDs and source observation
IDs remain attached for traceability.

A transfer rule is a hypothesis about which component can help, not proof that
the transferred value is correct. Invalid candidates are counted as rejected.
The original process-role split remains authoritative.
