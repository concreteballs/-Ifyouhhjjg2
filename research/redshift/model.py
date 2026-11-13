"""Candidate mappings from a driver variable to fractional clock shift."""
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
from math import isfinite
from research.return_flow.model import ReturnFlowInputs, calculate_return_flow

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
        coefficient=__import__("decimal").Decimal(str(return_coefficient)),
        exponent=__import__("decimal").Decimal(str(return_exponent)),
        maximum_fraction=__import__("decimal").Decimal(str(return_maximum_fraction)),
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
