"""Candidate mappings from a driver variable to fractional clock shift."""
from __future__ import annotations
from dataclasses import dataclass
from math import isfinite

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
