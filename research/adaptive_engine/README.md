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
