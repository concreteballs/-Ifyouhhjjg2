# TIK-0 local-state bridge

This layer constructs the two local states required by the redshift bridge.

## Per-location input

A location is represented by `TIKLocalStateInputs`:

- `tik`: the existing finite-volume TIK-0 inputs (`V`, `N`, `v_c`, event transmission probability and event energy);
- `return_channel_coverage_fraction`: fraction of the local region served by the return channel;
- `return_probability`: probability that energy enters the return channel;
- `return_efficiency`: fraction retained by the return mechanism;
- `return_reference_power_density_w_m3`: normalization for the return response curve.

The return-channel coverage is intentionally NOT the TIK active-cell volume fraction. TIK has already multiplied incoming power density by its active-cell fraction. Applying that same fraction again would double-count the active geometry. The return channel has its own independently declared coverage.

## Calculation

For each location:

1. Run `research.tik0.calculate(tik)` to obtain incoming `power_density_w_m3`.
2. Feed that power density into `ReturnFlowInputs`.
3. Calculate returned and retained power densities.
4. Compare the returned power densities of locations A and B.
5. Normalize their difference by `redshift_reference_power_density_w_m3`.
6. Map the dimensionless contrast to a fractional frequency shift using the selected response curve.

`predict_from_tik0_local_states` performs steps 1–6. The two input states may have different geometry, transmission probability, event energy, or return-channel parameters.

## Fitting observations

`redshift_observation_from_tik0_states` creates a `RedshiftObservation` with input kind `tik0_local_state_contrast`. Such observations can be passed to `fit_redshift_models`. The fit scales must be selected for the actual units and magnitude of the dataset.

## Evidence and calibration boundary

The existing Pound–Rebka and optical-clock benchmark records contain reference gravitational-potential shifts and measured frequency shifts. They do not report TIK cell geometry, event transmission, event energy, or return-channel state. They therefore remain control observations with input kind `reference_potential_shift`; they cannot be relabelled as TIK observations or used to fit the TIK bridge without independently specified local states.

Synthetic tests verify wiring and dimensional bookkeeping only. A physical fit requires measured or independently constrained local-state inputs paired with clock observations. Parameter provenance remains `ASSUMED_OR_USER_SUPPLIED` or `ASSUMED_OR_FITTED` until independent validation data exist.
