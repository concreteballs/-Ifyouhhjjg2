# Adaptive Engine (research prototype)

The Adaptive Engine is the control and search layer above TIK-0, return-flow and response models.

## Current capabilities

- Extensible named entities with units, roles, metadata and optional bounds.
- Five response formula families: linear, power, saturating, quadratic and linear-plus-saturating.
- Deterministic coarse parameter search with local refinement and input/output scale-aware grids.
- Weighted fitting, perturbation-aware ranking and local stability checks.
- JSON registry for reproducible candidate configurations.
- End-to-end paired TIK integration using canonical TIK-0 and return-flow calculations.
- Temporal TIK fitting for return response, initial state and relaxation time.
- Bounded raw-input search over explicitly selected geometry, transmission, event-energy and return-channel fields.

## Bounded raw-input search

Each tunable field is scoped to one observation ID and one pair side (`state_a` or `state_b`). This avoids silently overwriting independent measurements. Search dimensions and total combinations are capped; invalid geometries are skipped and counted. The selected candidate and all valid alternatives are returned in deterministic score order.

See [RAW_TIK_SEARCH.md](RAW_TIK_SEARCH.md) for supported fields and usage.

## Operating principles

The target is practical stability and useful behavior under changed inputs. A fitted configuration is not assumed to be uniquely identified or generally applicable. Keep alternatives, use holdout observations, and test sensitivity before promoting a configuration.

## Process analogy, task transfer and safety

- Directional process profiles compare structure, function, conditions, regimes, I/O schemas, ranges and provenance axis by axis.
- Partial analogues transfer named shared components; reverse transfer is assessed separately.
- Tasks can be decomposed into operations, clustered by reusable primitives and composed into new transfer plans.
- Holdout assignment is group-aware and requires independent lineage. Partial analogues are marked as transfer-only; unknowns remain unresolved.
- Reference-based calibration reports residuals and valid operating range.
- Learned capability is separate from execution permission. Risk-based approval, authorized scope, sandboxing and physical interlocks are checked by a fail-closed policy gate.

See [PROCESS_TRANSFER_AND_SAFETY.md](PROCESS_TRANSFER_AND_SAFETY.md).

## Applicability-aware TIK research pipeline

`fit_tik_research_dataset` connects process profiles directly to paired TIK fitting:
1. Classify every observation against a model-family reference profile.
2. Fit return-flow and response parameters using only observations assigned `FIT`.
3. Keep `PARTIAL_TRANSFER` observations available as transfer material, without treating them as fit or direct validation data.
4. Evaluate the frozen selected fit against independent `HOLDOUT` observations without refitting.
5. Return predictions, per-observation errors, RMSE and weighted RMSE, plus all role assignments and unresolved IDs.

Fit and holdout groups are explicitly supplied. Provenance shared with any training observation prevents holdout promotion. A dataset with fewer than two eligible fit observations is rejected rather than silently broadening the training set.

See [TIK_RESEARCH_PIPELINE.md](TIK_RESEARCH_PIPELINE.md).

## Component-level transfer search

Partial analogues can now produce explicit, auditable parameter hints through
`TIKTransferRule`. A rule names the reusable component, source and target raw
parameter, source/target pair side, and candidate multiplier/offset transforms.
Hints from multiple analogues are combined deterministically into bounded
candidate grids. Each candidate is optimized using only the pipeline's FIT
observations; the frozen fit is then scored on its independent HOLDOUT set.
Partial observations remain proposal sources only, never fitting rows or
holdout evidence. Candidate provenance retains the contributing proposal IDs.

See [TIK_COMPONENT_TRANSFER_SEARCH.md](TIK_COMPONENT_TRANSFER_SEARCH.md).


## TIK transfer feedback and experiment history

`build_transfer_feedback` compares each frozen transferred candidate with the
original baseline on the same FIT and independent HOLDOUT sets. It records
score improvements, stability, component names and proposal lineage. Without
HOLDOUT, outcomes remain explicitly unverified. The append-only
`TransferFeedbackRegistry` exports/imports versioned JSON history and
component outcome statistics; duplicate experiment IDs are rejected.

Feedback never refits on HOLDOUT or promotes partial-transfer observations into
training. See [TIK_TRANSFER_FEEDBACK.md](TIK_TRANSFER_FEEDBACK.md).
