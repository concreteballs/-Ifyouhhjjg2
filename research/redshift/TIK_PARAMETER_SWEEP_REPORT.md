# TIK-0 two-location parameter sweep and independent clock-data study

## Result in brief

A first end-to-end candidate can be made consistent with three separate experimental sources using a two-stage calibration:

1. Fit the redshift coefficient (k) to the 14 published run gradients from Zheng et al. (2023), fixing the redshift exponent (alpha=1).
2. Fit the spatial transmission gradient (dp/dh) to the independent PTB chronometric-levelling result (2025 data release).
3. Keep Chou et al. (2010), the 33 cm optical-clock height-change experiment, completely out of fitting and use it as a held-out check.

For the baseline scenario (p_0=0.25), active-cell volume fraction 0.5, return-channel coverage 0.75, return probability 0.8, return efficiency 0.9, and return response coefficient 0.25, the sweep gives:

| Return response family | Return exponent | Fitted (dp/dh) (m⁻¹) | Fitted redshift (k) | Chou holdout / measured |
|---|---:|---:|---:|---:|
| Linear | 1.0 (not used) | −1.4602e−4 | 1.0583e−13 | 0.99493 |
| Power | 1.5 | −1.0007e−4 | 1.2354e−13 | 0.99493 |
| Power | 2.0 | −7.6093e−5 | 1.3539e−13 | 0.99493 |
| Saturating | 1.0 (not used) | −1.7191e−4 | 9.5617e−14 | 0.99493 |

The PTB point is matched by construction because it is the external calibration set. The Chou prediction is approximately (4.08\times10^{-17}), compared with the reported (4.1\times10^{-17}) and uncertainty (1.6\times10^{-17}). Its residual is far below one combined standard deviation.

## What was actually fitted

### Training: Zheng et al. 2023

The deposited process data contain 14 measurement-run gradients. Recalculation from those rows gives:

- weighted mean magnitude: (12.3624\times10^{-19}/\mathrm{cm});
- statistical uncertainty: (0.6810\times10^{-19}/\mathrm{cm});
- reported systematic uncertainty: (2.5\times10^{-19}/\mathrm{cm});
- combined uncertainty: (2.591\times10^{-19}/\mathrm{cm}).

The 14 runs are repeated measurements in one apparatus, not 14 independent experiments. The systematic term is retained in the training uncertainty.

### External calibration: PTB chronometric levelling

The PTB data release reports a clock-derived geopotential difference (3918.1\pm2.6\;\mathrm{m^2/s^2}) and an independent geodetic value (3915.88\pm0.30\;\mathrm{m^2/s^2}). The profile uses the geodetic potential as its coordinate input, converted to equivalent height by division by local (g). It does not use the 457 km horizontal separation as a vertical height.

The fitted spatial transmission gradient is negative in the chosen orientation: transmission probability decreases with increasing equivalent height. This sign is a fitted ansatz, not a measured TIK property.

### Held-out check: Chou et al. 2010

The 33 cm clock-height-change result was not used to fit either (k) or the transmission gradient. The candidate predicts approximately 99.5% of the measured central value, comfortably within the reported uncertainty.

## Two-point parameter sweep findings

The implementation now varies the two locations independently in:
- active-cell count (N);
- cell volume (v_c);
- observation volume (V);
- transmission probability (p);
- event energy (arepsilon_T);
- return-channel coverage;
- return probability;
- return efficiency.

The returned-power contrast is calculated after running the complete TIK-0 and return-flow calculation at both locations.


### One-at-a-time two-location perturbation

Baseline point A uses (V=1\,\mathrm{m^3}), (N=5), (v_c=0.1\,\mathrm{m^3}), (p=0.25), event energy (10^{-147}\,\mathrm{J}), return coverage 0.75, return probability 0.8, and return efficiency 0.9. Its calculated returned power density is approximately (7.4135\times10^{-2}\,\mathrm{W/m^3}).

Point B changes one parameter at a time. The table reports (x=(\Pi_{r,A}-\Pi_{r,B})/\Pi_{r,A}).

| Parameter changed at B | B returned power density (W/m³) | Normalized contrast x |
|---|---:|---:|
| Active-cell count 5 → 10 | 2.9654e−1 | −3.0000 |
| Cell volume ×1.5 | 1.6680e−1 | −1.2500 |
| Observation volume ×1.5 | 3.2949e−2 | +0.5556 |
| Transmission probability ×1.5 | 1.6680e−1 | −1.2500 |
| Event energy ×2 | 2.9654e−1 | −3.0000 |
| Return-channel coverage ×1.2 | 8.8962e−2 | −0.2000 |
| Return probability ×1.2 | 8.8962e−2 | −0.2000 |
| Return efficiency ×1.1 | 8.1549e−2 | −0.1000 |

This is a sensitivity map of the current equations, not evidence that these parameters actually vary between clock locations. It also shows why independent local measurements matter: several different parameter changes can produce the same normalized contrast.

## Identifiability findings

Several parameters cannot be recovered from clock redshift data alone under the current normalized model:

1. A common multiplicative change in event energy scales both returned powers and the reference returned power together; it cancels from the dimensionless contrast.
2. A common return-channel coverage, return probability, or return efficiency also cancels from the normalized contrast when identical at both locations.
3. The baseline transmission probability (p_0) and its spatial gradient are strongly scale-degenerate. In the tested profiles, changing (p_0) rescales the fitted gradient while leaving (k) and the held-out prediction almost unchanged.
4. Linear, power-law, and saturating return curves can all fit the PTB calibration and predict the Chou holdout almost identically. Current data do not distinguish those families.

These are useful results: they tell us which parameters require direct local measurements or experiments with multiple spatial scales. A fitted value is not automatically an independently measured physical parameter.

## Provenance

| Quantity | Status |
|---|---|
| Planck event-rate density | ASSUMED working hypothesis |
| Baseline geometry and event energy | ASSUMED |
| Baseline return-channel parameters | ASSUMED |
| Return response family | ASSUMED candidate |
| Redshift exponent (alpha=1) | ASSUMED fixed for this first calibration |
| Redshift coefficient (k) | FITTED on Zheng 2023 |
| Transmission gradient (dp/dh) | FITTED on PTB 2025 |
| Chou 2010 result | INDEPENDENT_HOLDOUT |
| Physical TIK mechanism | NOT VALIDATED |

The current result is an internally consistent candidate calibration, not validation of the underlying TIK mechanism. The next experiment must measure or independently constrain at least one of the currently degenerate local quantities, preferably return-flow density at both clock locations.

## Sources

- Zheng et al. (2023), paper: https://pmc.ncbi.nlm.nih.gov/articles/PMC10423269/
- Zheng et al. (2023), process data (14 run gradients): https://zenodo.org/records/8184043
- Chou et al. (2010), NIST publication: https://www.nist.gov/publications/relativity-and-optical-clocks ; DOI: https://doi.org/10.1126/science.1192720
- Grotti et al., PTB dataset: https://oar.ptb.de/resources/show/10.7795/720.20250315 ; article DOI: https://doi.org/10.1103/PhysRevApplied.21.L061001
