"""Transparent dimensional model for a provisional temporal-information coefficient.

This is a phenomenological calculator, not a validated physical theory.
Event energy is independent of rest mass. Ordinary cell grouping is additive.
"""
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal, getcontext
from typing import Any

getcontext().prec = 60
D = Decimal
G = D("6.67430e-11")
HBAR = D("1.054571817e-34")
C = D("299792458")


@dataclass(frozen=True)
class PlanckScales:
    time_s: Decimal
    length_m: Decimal
    volume_m3: Decimal
    energy_j: Decimal
    event_rate_per_m3_s: Decimal


@dataclass(frozen=True)
class ModelInputs:
    event_energy_j: Decimal | None
    transmission_probability: Decimal
    grouped_cell_count: int = 1
    reference_power_density_w_m3: Decimal | None = None


@dataclass(frozen=True)
class ModelResult:
    scales: PlanckScales
    event_rate_per_m3_s: Decimal
    power_density_w_m3: Decimal | None
    tik0: Decimal | None
    parameter_status: dict[str, str]
    interpretation: tuple[str, ...]
    calibration_target_w_m3: Decimal | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "planck_scales": {
                "time_s": str(self.scales.time_s),
                "length_m": str(self.scales.length_m),
                "volume_m3": str(self.scales.volume_m3),
                "energy_j": str(self.scales.energy_j),
                "one_event_per_planck_cell_rate_per_m3_s": str(self.scales.event_rate_per_m3_s),
            },
            "event_rate_per_m3_s": str(self.event_rate_per_m3_s),
            "power_density_w_m3": None if self.power_density_w_m3 is None else str(self.power_density_w_m3),
            "tik0": None if self.tik0 is None else str(self.tik0),
            "parameter_status": self.parameter_status,
            "interpretation": list(self.interpretation),
            "calibration_target_w_m3": None if self.calibration_target_w_m3 is None else str(self.calibration_target_w_m3),
        }


def planck_scales() -> PlanckScales:
    """Derive Planck scales from the declared constants."""
    length = (HBAR * G / (C ** 3)).sqrt()
    time = (HBAR * G / (C ** 5)).sqrt()
    volume = length ** 3
    energy = (HBAR * (C ** 5) / G).sqrt()
    return PlanckScales(time, length, volume, energy, D(1) / (volume * time))


def _validate(inputs: ModelInputs) -> None:
    if not D(0) <= inputs.transmission_probability <= D(1):
        raise ValueError("transmission_probability must be between 0 and 1")
    if not isinstance(inputs.grouped_cell_count, int) or inputs.grouped_cell_count < 1:
        raise ValueError("grouped_cell_count must be a positive integer")
    if inputs.event_energy_j is not None and inputs.event_energy_j < 0:
        raise ValueError("event_energy_j cannot be negative")
    if inputs.reference_power_density_w_m3 is not None and inputs.reference_power_density_w_m3 <= 0:
        raise ValueError("reference_power_density_w_m3 must be positive")


def calculate(inputs: ModelInputs) -> ModelResult:
    """Calculate throughput, power density, and optional dimensionless TIK.

    Every grouped cell contributes the same baseline event rate. No nonlinear
    enhancement is assumed. The membrane-breakthrough regime is not modeled.
    """
    _validate(inputs)
    scales = planck_scales()
    rate = scales.event_rate_per_m3_s * inputs.transmission_probability * D(inputs.grouped_cell_count)
    power = None if inputs.event_energy_j is None else rate * inputs.event_energy_j
    tik = None if power is None or inputs.reference_power_density_w_m3 is None else power / inputs.reference_power_density_w_m3
    status = {
        "planck_constants": "derived_from_declared_CODATA_constants",
        "minimum_interval_and_volume": "working_hypothesis",
        "event_energy_j": "unknown" if inputs.event_energy_j is None else "user_supplied_or_calibrated",
        "transmission_probability": "initial_assumption_or_user_supplied",
        "grouped_cell_count": "explicit_additive_model_input",
        "reference_power_density_w_m3": "unknown" if inputs.reference_power_density_w_m3 is None else "user_supplied_reference",
    }
    notes = (
        "Energy per event is independent of rest mass in this model.",
        "Ordinary grouping is additive; no superlinear enhancement is included.",
        "The 125 GeV resonance is not equated with the minimum event energy.",
        "A fitted parameter is not independent evidence for the target used in fitting.",
        "This output is a model calculation, not an experimental measurement.",
    )
    return ModelResult(scales, rate, power, tik, status, notes)


def calibrate_event_energy(target_power_density_w_m3: Decimal, transmission_probability: Decimal, grouped_cell_count: int = 1) -> Decimal:
    """Solve for event energy that reproduces a target; this is calibration, not validation."""
    if target_power_density_w_m3 <= 0:
        raise ValueError("target_power_density_w_m3 must be positive")
    if not D(0) < transmission_probability <= D(1):
        raise ValueError("transmission_probability must be greater than 0 and at most 1")
    if not isinstance(grouped_cell_count, int) or grouped_cell_count < 1:
        raise ValueError("grouped_cell_count must be a positive integer")
    scales = planck_scales()
    return target_power_density_w_m3 * scales.volume_m3 * scales.time_s / (transmission_probability * D(grouped_cell_count))
