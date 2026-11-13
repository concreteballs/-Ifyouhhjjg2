# Return Flow Model

**Status:** isolated research module; candidate equations are not declared physically correct.

## Purpose

Model the fraction of incoming TIK-0 power density that returns through a separate channel. Compare response curves and fit coefficients against supplied observations or synthetic datasets.

## Inputs and units

- incoming power density: W/m³;
- active volume fraction: dimensionless, [0, 1];
- return probability: dimensionless, [0, 1];
- return efficiency: dimensionless, [0, 1];
- reference power density: W/m³, positive;
- normalized load: incoming power density / reference power density.

The channel multiplier is active fraction × return probability × return efficiency. The load-response curve is modeled separately.

## Candidate equations

For normalized load x:

- Linear: min(cap, kx)
- Power: min(cap, kx^α)
- Saturating: cap × (1 − exp(−kx))
- Dynamic saturating: first-order relaxation toward the saturating target with time constant τ.

## Fitting

The `fit_models()` function performs deterministic grid search over coefficients, exponents and time constants. It returns every tested candidate ranked by RMSE plus an optional complexity penalty. The best fit is calibration, not independent validation. Grid values are configurable for later refinement.

## TIK-0 integration

Pass `power_density_w_m3` from a TIK-0 result as `incoming_power_density_w_m3`. No change to TIK-0 is required in this first pass.

## Parameter provenance

Keep assumptions, fitted coefficients and independently validated parameters distinct. A low training RMSE alone never changes FITTED into VALIDATED.
