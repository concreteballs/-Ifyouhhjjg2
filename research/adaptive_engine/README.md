# Adaptive Engine (research prototype)

The Adaptive Engine is the control and search layer above TIK-0, return-flow and response models.

## Current capabilities

- Extensible named entities with units, roles, metadata and optional bounds.
- Five response formula families: linear, power, saturating, quadratic and linear-plus-saturating.
- Deterministic coarse parameter search with local refinement and input/output scale-aware grids.
- Weighted fitting, perturbation-aware ranking and local stability checks.
- JSON registry for reproducible candidate configurations.
- End-to-end paired TIK integration: calculates both local states using the canonical TIK-0 and return-flow modules, then jointly searches return-curve and downstream response choices.

## End-to-end TIK use

```python
from decimal import Decimal as D
from research.tik0 import ModelInputs, TIKLocalStateInputs
from research.adaptive_engine import TIKPairObservation, fit_tik_pairs

def state(probability):
    return TIKLocalStateInputs(
        tik=ModelInputs(D("10"), 2, D("2"), D(str(probability)), D("1e-120")),
        return_channel_coverage_fraction=D("0.75"),
        return_probability=D("0.8"),
        return_efficiency=D("0.9"),
        return_reference_power_density_w_m3=D("1e-10"),
    )

pairs = (
    TIKPairObservation("p1", state(0.9), state(0.8), 0.1),
    TIKPairObservation("p2", state(0.8), state(0.6), 0.2),
)
result = fit_tik_pairs(pairs)
print(result.selected.return_model, result.selected.return_coefficient)
print(result.selected.response.formula, result.selected.response.parameters)
print(result.selected.stability)
```

## Boundaries and next work

The adapter searches return-model family, return coefficient/exponent, and downstream response family/parameters over supplied paired observations. Raw TIK geometry, event energy, transmission probability and return-channel inputs remain supplied rather than automatically changed. The next layer should add bounded search over explicitly selected raw inputs, temporal state fitting, train/validation splits and richer formula composition.

A fitted result is a candidate configuration, not a guarantee of generalization. The returned alternatives and stability report must be retained.
