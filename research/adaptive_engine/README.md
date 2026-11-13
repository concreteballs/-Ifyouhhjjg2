# Adaptive Engine (research prototype)

The Adaptive Engine is the first unified control layer above the existing TIK-0,
return-flow and redshift research calculators. It does not modify those calculators.

## Current capabilities

- Extensible named entities with units, roles, metadata and optional bounds.
- Five candidate response families: linear, power, saturating, quadratic and
  linear-plus-saturating.
- Deterministic coarse parameter search followed by local refinement.
- Weighted fitting and a perturbation-aware ranking score.
- Repeatability, finite-output and local input-sensitivity checks.
- JSON model registry for reproducible candidate configurations.
- One-call facade returning the selected candidate and ranked alternatives.

## Minimal use

```python
from research.adaptive_engine import Entity, EntitySet, Sample, run_adaptive

data = tuple(Sample(x, 2*x + 0.5) for x in (-2, -1, 0, 1, 2))
result = run_adaptive(data, EntitySet((Entity("gain", 1.0),)))
print(result.selected.formula, result.selected.parameters)
print(result.stability)
```

## Boundaries

This is an operational search layer, not yet an automatic symbolic formula generator.
Its current optimizer searches a declared family of formulas. Dynamic state-space
models, graph-based formula composition, automatic entity invention, robust
cross-validation and a persistent production database are subsequent extensions.
A fitted candidate is not automatically stable: callers must inspect the stability
report and choose acceptance thresholds appropriate to their use case.
