# Gravitational Redshift — Benchmark and TIK Bridge

**Status:** research prototype. Published benchmark data are independent of this project; the TIK return-flow mapping is not yet calibrated.

## What this module does

1. Stores published aggregate redshift measurements with uncertainties and source metadata.
2. Fits candidate response curves against a declared input variable.
3. Provides a separate function mapping a TIK return-flow contrast to a fractional clock shift.
4. Keeps reference-potential control fitting separate from TIK-flow fitting.

## Bundled benchmark data

- Pound–Rebka: 22.5 m tower, two-way differential result, measured (5.13 ± 0.51) × 10⁻¹⁵; quoted reference prediction 4.885 × 10⁻¹⁵.
- Zheng et al. (2023): 1 cm clock-gradient magnitude, measured 12.4 × 10⁻¹⁹/cm; expected 10.9 × 10⁻¹⁹/cm; combined uncertainty approximately 2.6 × 10⁻¹⁹/cm.

The observations use input_kind=reference_potential_shift and the reference prediction as x. The fitter evaluates how measured shifts compare with a reference-potential input. It does not prove that TIK-0 generates that input.

## Candidate curves

For signed normalized input x:
- Linear: y = kx
- Power: y = k sign(x)|x|ᵅ
- Saturating: y = sign(x) m(1 − exp(−rx))

The fitter minimizes uncertainty-weighted chi-squared and optionally penalizes model complexity. Fewer than three independent observations are marked UNDERDETERMINED.

## TIK return-flow bridge

predict_from_return_flow_contrast() accepts a difference in returned power density between two clock locations (W/m³), a positive reference power density (W/m³), and fitted coefficient k and exponent α. It forms dimensionless x = ΔΠ_return / Π_reference and predicts y = k sign(x)|x|ᵅ.

The benchmark papers do not report ΔΠ_return, so a TIK-flow fit is intentionally not fabricated. The next missing model input is a rule that computes return-flow contrast at each clock location from TIK-0 cell geometry, transmission probability, event energy and return parameters.

## Provenance

Benchmark values are PUBLISHED_MEASUREMENT or PUBLISHED_REFERENCE. Grid-selected parameters are FITTED. The TIK bridge structure is ASSUMED. A fitted curve is not VALIDATED until tested against independent observations not used for fitting.
