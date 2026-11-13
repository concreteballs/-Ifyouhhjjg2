"""Candidate mappings from a driver variable to fractional clock shift."""
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
from math import isfinite
from research.return_flow.model import ReturnFlowInputs, calculate_return_flow
from research.tik0.local_state import TIKLocalStateInputs, calculate_local_state

@dataclass(frozen=True)
class RedshiftObservation:
    name: str
    x: float
    y: float
    sigma: float
    input_kind: str
    source: str = ""
    source_url: str = ""
    source_doi: str = ""
    notes: str = ""

@dataclass(frozen=True)
class RedshiftPrediction:
    fractional_shift: float
    input_kind: str
    model_name: str
    parameter_status: str = "ASSUMED_OR_FITTED"

def _finite(value: float, label: str) -> None:
    if not isfinite(value):
        raise ValueError(label + " must be finite")

def predict_from_reference_shift(reference_fractional_shift: float, *, coefficient: float = 1.0) -> RedshiftPrediction:
    """Control model: measured shift = coefficient × reference shift."""
    _finite(reference_fractional_shift, "reference_fractional_shift")
    _finite(coefficient, "coefficient")
    if coefficient < 0:
        raise ValueError("coefficient must be non-negative")
    return RedshiftPrediction(coefficient * reference_fractional_shift, "reference_potential_shift", "linear_reference_control")

def predict_from_return_flow_contrast(delta_return_power_density_w_m3: float, reference_power_density_w_m3: float, *, coefficient: float = 1.0, exponent: float = 1.0) -> RedshiftPrediction:
    """Map return-flow contrast to fractional clock shift.

    x = delta returned power density / reference power density is dimensionless.
    The published benchmark papers do not report this return-flow contrast,
    so this bridge cannot yet be calibrated from the bundled observations.
    """
    for value, label in (
        (delta_return_power_density_w_m3, "delta_return_power_density_w_m3"),
        (reference_power_density_w_m3, "reference_power_density_w_m3"),
        (coefficient, "coefficient"), (exponent, "exponent"),
    ):
        _finite(value, label)
    if reference_power_density_w_m3 <= 0:
        raise ValueError("reference_power_density_w_m3 must be positive")
    if coefficient < 0 or exponent <= 0:
        raise ValueError("coefficient must be non-negative and exponent positive")
    x = delta_return_power_density_w_m3 / reference_power_density_w_m3
    shift = coefficient * (1.0 if x >= 0 else -1.0) * (abs(x) ** exponent)
    return RedshiftPrediction(shift, "return_flow_contrast", "power_law_return_flow")

def predict_from_return_flow_states(
    location_a: ReturnFlowInputs,
    location_b: ReturnFlowInputs,
    *,
    reference_power_density_w_m3: float,
    return_model_name: str = "linear",
    return_coefficient: float = 1.0,
    return_exponent: float = 1.0,
    return_maximum_fraction: float = 1.0,
    redshift_coefficient: float = 1.0,
    redshift_exponent: float = 1.0,
) -> RedshiftPrediction:
    """Run TIK return-flow calculations at two locations and map their contrast.

    This is the explicit TIK-0 → return-flow → redshift calculation path.
    Location-specific ReturnFlowInputs must be supplied by the caller; the
    bundled experimental benchmarks do not contain these TIK state variables.
    """
    flow_a = calculate_return_flow(
        location_a, model_name=return_model_name,
        coefficient=Decimal(str(return_coefficient)),
        exponent=Decimal(str(return_exponent)),
        maximum_fraction=Decimal(str(return_maximum_fraction)),
    )
    flow_b = calculate_return_flow(
        location_b, model_name=return_model_name,
        coefficient=Decimal(str(return_coefficient)),
        exponent=Decimal(str(return_exponent)),
        maximum_fraction=Decimal(str(return_maximum_fraction)),
    )
    delta = float(flow_a.returned_power_density_w_m3 - flow_b.returned_power_density_w_m3)
    prediction = predict_from_return_flow_contrast(
        delta, reference_power_density_w_m3,
        coefficient=redshift_coefficient, exponent=redshift_exponent,
    )
    return RedshiftPrediction(
        prediction.fractional_shift,
        prediction.input_kind,
        "tik0_return_flow_" + return_model_name,
        prediction.parameter_status,
    )


def _local_return_density(
    state: TIKLocalStateInputs,
    *,
    return_model_name: str,
    return_coefficient: float,
    return_exponent: float,
    return_maximum_fraction: float,
) -> float:
    result = calculate_local_state(
        state,
        return_model_name=return_model_name,
        return_coefficient=Decimal(str(return_coefficient)),
        return_exponent=Decimal(str(return_exponent)),
        return_maximum_fraction=Decimal(str(return_maximum_fraction)),
    )
    return float(result.return_flow.returned_power_density_w_m3)


def predict_from_tik0_local_states(
    location_a: TIKLocalStateInputs,
    location_b: TIKLocalStateInputs,
    *,
    redshift_reference_power_density_w_m3: float,
    return_model_name: str = "linear",
    return_coefficient: float = 1.0,
    return_exponent: float = 1.0,
    return_maximum_fraction: float = 1.0,
    redshift_coefficient: float = 1.0,
    redshift_exponent: float = 1.0,
) -> RedshiftPrediction:
    """End-to-end TIK-0 -> return-flow -> fractional clock-shift prediction."""
    returned_a = _local_return_density(
        location_a, return_model_name=return_model_name,
        return_coefficient=return_coefficient, return_exponent=return_exponent,
        return_maximum_fraction=return_maximum_fraction,
    )
    returned_b = _local_return_density(
        location_b, return_model_name=return_model_name,
        return_coefficient=return_coefficient, return_exponent=return_exponent,
        return_maximum_fraction=return_maximum_fraction,
    )
    result = predict_from_return_flow_contrast(
        returned_a - returned_b, redshift_reference_power_density_w_m3,
        coefficient=redshift_coefficient, exponent=redshift_exponent,
    )
    return RedshiftPrediction(
        result.fractional_shift, "tik0_local_state_contrast",
        "tik0_local_state_" + return_model_name, result.parameter_status,
    )


def redshift_observation_from_tik0_states(
    name: str,
    location_a: TIKLocalStateInputs,
    location_b: TIKLocalStateInputs,
    *,
    observed_fractional_shift: float,
    sigma: float,
    redshift_reference_power_density_w_m3: float,
    return_model_name: str = "linear",
    return_coefficient: float = 1.0,
    return_exponent: float = 1.0,
    return_maximum_fraction: float = 1.0,
    source: str = "",
    source_url: str = "",
    source_doi: str = "",
    notes: str = "",
) -> RedshiftObservation:
    """Create a fit observation only when both local TIK states are specified.

    The x value is the dimensionless returned-power-density contrast. It is
    intentionally not the gravitational-potential control variable.
    """
    if redshift_reference_power_density_w_m3 <= 0:
        raise ValueError("redshift_reference_power_density_w_m3 must be positive")
    if sigma <= 0:
        raise ValueError("sigma must be positive")
    returned_a = _local_return_density(
        location_a, return_model_name=return_model_name,
        return_coefficient=return_coefficient, return_exponent=return_exponent,
        return_maximum_fraction=return_maximum_fraction,
    )
    returned_b = _local_return_density(
        location_b, return_model_name=return_model_name,
        return_coefficient=return_coefficient, return_exponent=return_exponent,
        return_maximum_fraction=return_maximum_fraction,
    )
    return RedshiftObservation(
        name=name,
        x=(returned_a - returned_b) / redshift_reference_power_density_w_m3,
        y=observed_fractional_shift,
        sigma=sigma,
        input_kind="tik0_local_state_contrast",
        source=source,
        source_url=source_url,
        source_doi=source_doi,
        notes=notes or "TIK-0 local-state contrast; not a reference-potential input.",
    )
