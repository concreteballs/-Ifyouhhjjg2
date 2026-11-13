# Bounded raw TIK input search

This layer searches actual TIK-0 and return-channel inputs before fitting the downstream response. Each candidate is evaluated by the existing `fit_tik_pairs` adapter; no duplicate TIK calculation is introduced.

## Explicit target scope

Every grid names exactly one observation ID, one pair side (`state_a` or `state_b`) and one parameter. A candidate never silently overwrites every observation or both sides of a pair.

Supported fields:
- TIK geometry: `observation_volume_m3`, `active_cell_count`, `cell_volume_m3`;
- TIK input: `transmission_probability`, `event_energy_j`;
- return channel: `return_channel_coverage_fraction`, `return_probability`, `return_efficiency`, `return_reference_power_density_w_m3`.

## Example

```python
from research.adaptive_engine.raw_parameter_search import TIKRawParameterGrid, fit_tik_raw_parameters

grids = (
    TIKRawParameterGrid("pair-1", "state_a", "transmission_probability", (0.65, 0.75, 0.85, 0.95)),
    TIKRawParameterGrid("pair-2", "state_b", "return_efficiency", (0.70, 0.80, 0.90)),
)
result = fit_tik_raw_parameters(observations, grids)
print(result.selected.parameter_values)
print(result.selected.fit.selected)
print(result.attempted_count, result.rejected_count)
```

## Search controls

- Four tunable dimensions and 256 combinations by default.
- The combination budget is checked before the search starts.
- Every candidate passes through canonical TIK/local-state validation.
- Invalid geometry or probability combinations are skipped and counted.
- Valid candidates are ranked by the paired adapter score, including its stability penalty.
- Selected candidate and all valid alternatives are returned deterministically.
- Input observations are immutable and unchanged.

This is a bounded fitting mechanism, not a claim that parameters are uniquely identified. Retain alternatives and test selected configurations on separate observations before promoting them.
