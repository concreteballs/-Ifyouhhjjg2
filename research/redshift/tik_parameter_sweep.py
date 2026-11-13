"""Two-location TIK parameter sweeps and cross-experiment profile calibration.

The height-linked transmission profile is an explicit candidate ansatz:
p(h) = p0 + gradient * h. It is not an experimentally measured TIK field.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import Decimal
from math import sqrt
from typing import Literal

from research.tik0 import ModelInputs, TIKLocalStateInputs, calculate_local_state
from .independent_benchmarks import (
    CHOU_2010_HOLDOUT,
    PTB_2025_CALIBRATION,
    ZHENG_2023_TRAINING,
)

D = Decimal
ReturnModel = Literal["linear", "power", "saturating"]


@dataclass(frozen=True)
class TIKHeightProfile:
    base_state: TIKLocalStateInputs
    transmission_gradient_per_m: Decimal


@dataclass(frozen=True)
class TIKContrast:
    lower_return_power_density_w_m3: Decimal
    upper_return_power_density_w_m3: Decimal
    reference_return_power_density_w_m3: Decimal
    normalized_contrast: Decimal
    lower_transmission_probability: Decimal
    upper_transmission_probability: Decimal


@dataclass(frozen=True)
class ProfileCalibration:
    return_model: str
    return_coefficient: float
    return_exponent: float
    baseline_transmission_probability: float
    fitted_transmission_gradient_per_m: float
    fitted_redshift_coefficient: float
    redshift_exponent: float
    training_prediction: float
    external_calibration_prediction: float
    external_calibration_observed: float
    holdout_prediction: float
    holdout_observed: float
    holdout_sigma: float
    holdout_residual_sigma: float
    transmission_probability_at_holdout_height: float
    status: dict[str, str]


@dataclass(frozen=True)
class ParameterEffect:
    parameter: str
    baseline_value: str
    varied_value: str
    returned_power_density_a_w_m3: str
    returned_power_density_b_w_m3: str
    normalized_contrast: str


def build_reference_state(
    *,
    transmission_probability: Decimal = D("0.25"),
    active_volume_fraction: Decimal = D("0.5"),
    return_channel_coverage_fraction: Decimal = D("0.75"),
    return_probability: Decimal = D("0.8"),
    return_efficiency: Decimal = D("0.9"),
    event_energy_j: Decimal = D("1e-147"),
) -> TIKLocalStateInputs:
    """Create a finite-volume baseline; common scale factors are deliberately explicit."""
    if not D(0) < active_volume_fraction <= D(1):
        raise ValueError("active_volume_fraction must be in (0, 1]")
    tik = ModelInputs(
        observation_volume_m3=D("1"),
        active_cell_count=5,
        cell_volume_m3=active_volume_fraction / D(5),
        transmission_probability=transmission_probability,
        event_energy_j=event_energy_j,
    )
    from research.tik0 import calculate
    incoming = calculate(tik).power_density_w_m3
    if incoming is None or incoming <= 0:
        raise ValueError("baseline TIK incoming power density must be positive")
    return TIKLocalStateInputs(
        tik=tik,
        return_channel_coverage_fraction=return_channel_coverage_fraction,
        return_probability=return_probability,
        return_efficiency=return_efficiency,
        return_reference_power_density_w_m3=incoming,
    )


def state_at_height(profile: TIKHeightProfile, height_m: Decimal) -> TIKLocalStateInputs:
    probability = (
        profile.base_state.tik.transmission_probability
        + profile.transmission_gradient_per_m * height_m
    )
    if not D(0) <= probability <= D(1):
        raise ValueError("height profile produces a transmission probability outside [0, 1]")
    return replace(
        profile.base_state,
        tik=replace(profile.base_state.tik, transmission_probability=probability),
    )


def calculate_profile_contrast(
    profile: TIKHeightProfile,
    lower_height_m: Decimal,
    upper_height_m: Decimal,
    *,
    return_model: ReturnModel = "linear",
    return_coefficient: Decimal = D("0.25"),
    return_exponent: Decimal = D("1.5"),
    return_maximum_fraction: Decimal = D("1"),
) -> TIKContrast:
    if upper_height_m <= lower_height_m:
        raise ValueError("upper_height_m must be greater than lower_height_m")
    lower_state = state_at_height(profile, lower_height_m)
    upper_state = state_at_height(profile, upper_height_m)
    base_result = calculate_local_state(
        profile.base_state,
        return_model_name=return_model,
        return_coefficient=return_coefficient,
        return_exponent=return_exponent,
        return_maximum_fraction=return_maximum_fraction,
    )
    lower_result = calculate_local_state(
        lower_state,
        return_model_name=return_model,
        return_coefficient=return_coefficient,
        return_exponent=return_exponent,
        return_maximum_fraction=return_maximum_fraction,
    )
    upper_result = calculate_local_state(
        upper_state,
        return_model_name=return_model,
        return_coefficient=return_coefficient,
        return_exponent=return_exponent,
        return_maximum_fraction=return_maximum_fraction,
    )
    reference = base_result.return_flow.returned_power_density_w_m3
    if reference <= 0:
        raise ValueError("baseline returned power density must be positive")
    # Orientation: lower minus upper. A decreasing transmission profile gives
    # a positive driver for the positive clock-shift magnitude used here.
    contrast = (
        lower_result.return_flow.returned_power_density_w_m3
        - upper_result.return_flow.returned_power_density_w_m3
    ) / reference
    return TIKContrast(
        lower_result.return_flow.returned_power_density_w_m3,
        upper_result.return_flow.returned_power_density_w_m3,
        reference,
        contrast,
        lower_state.tik.transmission_probability,
        upper_state.tik.transmission_probability,
    )


def _predict_ratio_for_gradient(
    base_state: TIKLocalStateInputs,
    gradient: float,
    *,
    return_model: ReturnModel,
    return_coefficient: float,
    return_exponent: float,
    redshift_exponent: float,
) -> tuple[float, float, float]:
    profile = TIKHeightProfile(base_state, D(str(gradient)))
    x_train = float(calculate_profile_contrast(
        profile, D("0"), D(str(ZHENG_2023_TRAINING.height_equivalent_m)),
        return_model=return_model,
        return_coefficient=D(str(return_coefficient)),
        return_exponent=D(str(return_exponent)),
    ).normalized_contrast)
    x_ptb = float(calculate_profile_contrast(
        profile, D("0"), D(str(PTB_2025_CALIBRATION.height_equivalent_m)),
        return_model=return_model,
        return_coefficient=D(str(return_coefficient)),
        return_exponent=D(str(return_exponent)),
    ).normalized_contrast)
    if x_train <= 0 or x_ptb <= 0:
        raise ValueError("selected profile orientation must produce positive contrasts")
    y_train = ZHENG_2023_TRAINING.observed_fractional_shift
    coefficient = y_train / (x_train ** redshift_exponent)
    prediction = coefficient * (x_ptb ** redshift_exponent)
    return prediction, coefficient, x_train


def calibrate_profile_to_independent_data(
    *,
    baseline_transmission_probability: float = 0.25,
    active_volume_fraction: float = 0.5,
    return_channel_coverage_fraction: float = 0.75,
    return_probability: float = 0.8,
    return_efficiency: float = 0.9,
    event_energy_j: float = 1e-147,
    return_model: ReturnModel = "linear",
    return_coefficient: float = 0.25,
    return_exponent: float = 1.5,
    redshift_exponent: float = 1.0,
) -> ProfileCalibration:
    """Fit the spatial transmission gradient on PTB after calibrating k on Zheng.

    Alpha is held fixed (default 1) because the available independent training
    gradient is a single spatial scale. PTB determines the profile gradient;
    Chou remains a held-out experiment.
    """
    base = build_reference_state(
        transmission_probability=D(str(baseline_transmission_probability)),
        active_volume_fraction=D(str(active_volume_fraction)),
        return_channel_coverage_fraction=D(str(return_channel_coverage_fraction)),
        return_probability=D(str(return_probability)),
        return_efficiency=D(str(return_efficiency)),
        event_energy_j=D(str(event_energy_j)),
    )
    target = PTB_2025_CALIBRATION.observed_fractional_shift
    p0 = baseline_transmission_probability
    h_ptb = PTB_2025_CALIBRATION.height_equivalent_m
    low = -0.9 * p0 / h_ptb
    high = -1e-12

    def residual(gradient: float) -> float:
        predicted, _, _ = _predict_ratio_for_gradient(
            base, gradient, return_model=return_model,
            return_coefficient=return_coefficient,
            return_exponent=return_exponent,
            redshift_exponent=redshift_exponent,
        )
        return predicted - target

    r_low, r_high = residual(low), residual(high)
    if r_low * r_high > 0:
        raise ValueError("PTB target is outside the selected profile's calibration range")
    for _ in range(90):
        middle = (low + high) / 2.0
        r_middle = residual(middle)
        if r_middle > 0:
            high = middle
        else:
            low = middle
    gradient = (low + high) / 2.0
    predicted_ptb, coefficient, x_train = _predict_ratio_for_gradient(
        base, gradient, return_model=return_model,
        return_coefficient=return_coefficient,
        return_exponent=return_exponent,
        redshift_exponent=redshift_exponent,
    )
    profile = TIKHeightProfile(base, D(str(gradient)))
    x_chou = float(calculate_profile_contrast(
        profile, D("0"), D(str(CHOU_2010_HOLDOUT.height_equivalent_m)),
        return_model=return_model,
        return_coefficient=D(str(return_coefficient)),
        return_exponent=D(str(return_exponent)),
    ).normalized_contrast)
    prediction_chou = coefficient * (x_chou ** redshift_exponent)
    train_relative_sigma = (
        ZHENG_2023_TRAINING.observed_sigma
        / ZHENG_2023_TRAINING.observed_fractional_shift
    )
    combined_holdout_sigma = sqrt(
        CHOU_2010_HOLDOUT.observed_sigma**2
        + (prediction_chou * train_relative_sigma)**2
    )
    holdout_z = (
        prediction_chou - CHOU_2010_HOLDOUT.observed_fractional_shift
    ) / combined_holdout_sigma
    p_holdout = (
        baseline_transmission_probability
        + gradient * PTB_2025_CALIBRATION.height_equivalent_m
    )
    return ProfileCalibration(
        return_model=return_model,
        return_coefficient=return_coefficient,
        return_exponent=return_exponent,
        baseline_transmission_probability=baseline_transmission_probability,
        fitted_transmission_gradient_per_m=gradient,
        fitted_redshift_coefficient=coefficient,
        redshift_exponent=redshift_exponent,
        training_prediction=ZHENG_2023_TRAINING.observed_fractional_shift,
        external_calibration_prediction=predicted_ptb,
        external_calibration_observed=target,
        holdout_prediction=prediction_chou,
        holdout_observed=CHOU_2010_HOLDOUT.observed_fractional_shift,
        holdout_sigma=combined_holdout_sigma,
        holdout_residual_sigma=holdout_z,
        transmission_probability_at_holdout_height=p_holdout,
        status={
            "baseline_geometry": "ASSUMED",
            "event_energy": "ASSUMED",
            "baseline_transmission_probability": "ASSUMED",
            "return_channel_parameters": "ASSUMED",
            "return_response_family": "ASSUMED_CANDIDATE",
            "return_response_parameters": "ASSUMED",
            "redshift_exponent": "ASSUMED_FIXED",
            "redshift_coefficient": "FITTED_ON_ZHENG_2023",
            "transmission_gradient": "FITTED_ON_PTB_2025",
            "chou_2010_holdout": "INDEPENDENT_HOLDOUT",
        },
    )


def run_default_parameter_sweep() -> list[ProfileCalibration]:
    """Compare return families/exponents and baseline transmission values."""
    results: list[ProfileCalibration] = []
    for p0 in (0.1, 0.25, 0.5, 0.75):
        results.append(calibrate_profile_to_independent_data(
            baseline_transmission_probability=p0,
            return_model="linear", return_coefficient=0.25,
        ))
        for exponent in (1.0, 1.5, 2.0):
            results.append(calibrate_profile_to_independent_data(
                baseline_transmission_probability=p0,
                return_model="power", return_coefficient=0.25,
                return_exponent=exponent,
            ))
        for coefficient in (0.1, 0.25, 0.5):
            results.append(calibrate_profile_to_independent_data(
                baseline_transmission_probability=p0,
                return_model="saturating", return_coefficient=coefficient,
            ))
    return results


def sweep_two_point_parameters(
    base_state: TIKLocalStateInputs | None = None,
) -> list[ParameterEffect]:
    """Perturb one local parameter at point B while point A remains the baseline."""
    base = base_state or build_reference_state()
    base_result = calculate_local_state(
        base, return_model_name="linear", return_coefficient=D("0.25")
    )
    reference = base_result.return_flow.returned_power_density_w_m3
    if reference <= 0:
        raise ValueError("baseline returned power density must be positive")

    cases: list[tuple[str, str, TIKLocalStateInputs]] = []

    def add(name: str, value: str, state: TIKLocalStateInputs) -> None:
        cases.append((name, value, state))

    add("active_cell_count", "10", replace(
        base, tik=replace(base.tik, active_cell_count=10)
    ))
    add("cell_volume_m3", "1.5x", replace(
        base, tik=replace(base.tik, cell_volume_m3=base.tik.cell_volume_m3 * D("1.5"))
    ))
    add("observation_volume_m3", "1.5x", replace(
        base, tik=replace(base.tik, observation_volume_m3=base.tik.observation_volume_m3 * D("1.5"))
    ))
    add("transmission_probability", "1.5x", replace(
        base, tik=replace(base.tik, transmission_probability=base.tik.transmission_probability * D("1.5"))
    ))
    add("event_energy_j", "2x", replace(
        base, tik=replace(base.tik, event_energy_j=base.tik.event_energy_j * D("2"))
    ))
    add("return_channel_coverage_fraction", "1.2x", replace(
        base, return_channel_coverage_fraction=base.return_channel_coverage_fraction * D("1.2")
    ))
    add("return_probability", "1.2x", replace(
        base, return_probability=base.return_probability * D("1.2")
    ))
    add("return_efficiency", "1.1x", replace(
        base, return_efficiency=base.return_efficiency * D("1.1")
    ))

    effects: list[ParameterEffect] = []
    for name, value, state_b in cases:
        result_b = calculate_local_state(
            state_b, return_model_name="linear", return_coefficient=D("0.25")
        )
        contrast = (base_result.return_flow.returned_power_density_w_m3
                    - result_b.return_flow.returned_power_density_w_m3) / reference
        effects.append(ParameterEffect(
            parameter=name,
            baseline_value="baseline",
            varied_value=value,
            returned_power_density_a_w_m3=str(base_result.return_flow.returned_power_density_w_m3),
            returned_power_density_b_w_m3=str(result_b.return_flow.returned_power_density_w_m3),
            normalized_contrast=str(contrast),
        ))
    return effects
