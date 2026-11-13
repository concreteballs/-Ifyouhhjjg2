"""Dimensionally explicit TIK-0 phenomenological calculator.

This is an exploratory bookkeeping model, not a validated physical theory.
The Planck event-rate density is a provisional hypothesis, not an observation.
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
    observation_volume_m3: Decimal
    active_cell_count: int
    cell_volume_m3: Decimal
    transmission_probability: Decimal
    event_energy_j: Decimal | None = None
    reference_power_density_w_m3: Decimal | None = None


@dataclass(frozen=True)
class ModelResult:
    scales: PlanckScales
    active_volume_m3: Decimal
    active_volume_fraction: Decimal
    total_event_rate_per_s: Decimal
    event_rate_density_per_m3_s: Decimal
    total_power_w: Decimal | None
    power_density_w_m3: Decimal | None
    tik0: Decimal | None
    parameter_status: dict[str, str]
    interpretation: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "planck_scales": {
                "time_s": str(self.scales.time_s),
                "length_m": str(self.scales.length_m),
                "volume_m3": str(self.scales.volume_m3),
                "energy_j": str(self.scales.energy_j),
                "provisional_event_rate_density_per_m3_s": str(self.scales.event_rate_per_m3_s),
            },
            "active_volume_m3": str(self.active_volume_m3),
            "active_volume_fraction": str(self.active_volume_fraction),
            "total_event_rate_per_s": str(self.total_event_rate_per_s),
            "event_rate_density_per_m3_s": str(self.event_rate_density_per_m3_s),
            "total_power_w": None if self.total_power_w is None else str(self.total_power_w),
            "power_density_w_m3": None if self.power_density_w_m3 is None else str(self.power_density_w_m3),
            "tik0": None if self.tik0 is None else str(self.tik0),
            "parameter_status": dict(self.parameter_status),
            "interpretation": list(self.interpretation),
        }


def planck_scales() -> PlanckScales:
    """Derive Planck scales from the declared constants."""
    length = (HBAR * G / (C ** 3)).sqrt()
    time = (HBAR * G / (C ** 5)).sqrt()
    volume = length ** 3
    energy = (HBAR * (C ** 5) / G).sqrt()
    return PlanckScales(time, length, volume, energy, D(1) / (volume * time))


def _validate(inputs: ModelInputs) -> None:
    if inputs.observation_volume_m3 <= 0:
        raise ValueError("observation_volume_m3 must be positive")
    if not isinstance(inputs.active_cell_count, int) or isinstance(inputs.active_cell_count, bool) or inputs.active_cell_count < 1:
        raise ValueError("active_cell_count must be a positive integer")
    if inputs.cell_volume_m3 <= 0:
        raise ValueError("cell_volume_m3 must be positive")
    active_volume = D(inputs.active_cell_count) * inputs.cell_volume_m3
    if active_volume > inputs.observation_volume_m3:
        raise ValueError("active cell volume cannot exceed observation volume")
    if not D(0) <= inputs.transmission_probability <= D(1):
        raise ValueError("transmission_probability must be between 0 and 1")
    if inputs.event_energy_j is not None and inputs.event_energy_j < 0:
        raise ValueError("event_energy_j cannot be negative")
    if inputs.reference_power_density_w_m3 is not None and inputs.reference_power_density_w_m3 <= 0:
        raise ValueError("reference_power_density_w_m3 must be positive")


def calculate(inputs: ModelInputs) -> ModelResult:
    """Calculate event throughput and optional power density and TIK-0.

    Each active cell contributes in proportion to its effective volume.
    Regrouping or subdividing an unchanged active volume has no effect.
    """
    _validate(inputs)
    scales = planck_scales()
    active_volume = D(inputs.active_cell_count) * inputs.cell_volume_m3
    active_fraction = active_volume / inputs.observation_volume_m3
    total_rate = scales.event_rate_per_m3_s * inputs.transmission_probability * active_volume
    rate_density = total_rate / inputs.observation_volume_m3
    total_power = None if inputs.event_energy_j is None else total_rate * inputs.event_energy_j
    power_density = None if total_power is None else total_power / inputs.observation_volume_m3
    tik = (
        None
        if power_density is None or inputs.reference_power_density_w_m3 is None
        else power_density / inputs.reference_power_density_w_m3
    )
    status = {
        "planck_constants": "derived_from_declared_constants",
        "one_candidate_event_per_planck_volume_per_planck_time": "working_hypothesis",
        "observation_volume_m3": "user_supplied_finite_region",
        "active_cell_count": "user_supplied_positive_integer",
        "cell_volume_m3": "user_supplied_fixed_effective_volume",
        "transmission_probability": "user_supplied_event_pass_probability",
        "event_energy_j": "unknown" if inputs.event_energy_j is None else "user_supplied_or_calibrated",
        "reference_power_density_w_m3": "unknown" if inputs.reference_power_density_w_m3 is None else "user_supplied_reference",
    }
    notes = (
        "The Planck-scale event-rate density is a provisional model assumption, not an established physical event rate.",
        "Active-cell contributions are additive and proportional to disjoint effective cell volume.",
        "Regrouping or subdividing an unchanged active volume does not change throughput.",
        "Energy per event is independent of rest mass in this model.",
        "Energy density (J/m3) and power density (W/m3) are not interchangeable.",
        "Calibration reproducing a target is not independent validation.",
        "Membrane breakthrough and black-hole regimes are outside this calculator.",
        "This output is a model calculation, not an experimental measurement.",
    )
    return ModelResult(
        scales, active_volume, active_fraction, total_rate, rate_density,
        total_power, power_density, tik, status, notes,
    )


def calibrate_event_energy(
    target_power_density_w_m3: Decimal,
    observation_volume_m3: Decimal,
    active_cell_count: int,
    cell_volume_m3: Decimal,
    transmission_probability: Decimal,
) -> Decimal:
    """Fit event energy to a target power density; this is calibration, not validation."""
    if target_power_density_w_m3 <= 0:
        raise ValueError("target_power_density_w_m3 must be positive")
    geometry = ModelInputs(
        observation_volume_m3=observation_volume_m3,
        active_cell_count=active_cell_count,
        cell_volume_m3=cell_volume_m3,
        transmission_probability=transmission_probability,
    )
    _validate(geometry)
    if transmission_probability == 0:
        raise ValueError("transmission_probability must be greater than 0 for calibration")
    result = calculate(geometry)
    if result.event_rate_density_per_m3_s == 0:
        raise ValueError("event rate density must be positive for calibration")
    return target_power_density_w_m3 / result.event_rate_density_per_m3_s
