"""Dimensionally explicit return-flow model variants."""
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
from math import exp
from typing import Literal

D = Decimal
ModelName = Literal["linear", "power", "saturating"]

@dataclass(frozen=True)
class ReturnFlowInputs:
    incoming_power_density_w_m3: Decimal
    active_volume_fraction: Decimal
    return_probability: Decimal
    return_efficiency: Decimal = D("1")
    reference_power_density_w_m3: Decimal = D("1")

@dataclass(frozen=True)
class ReturnFlowResult:
    normalized_load: Decimal
    return_fraction: Decimal
    returned_power_density_w_m3: Decimal
    retained_power_density_w_m3: Decimal
    model_name: str
    parameter_status: dict[str, str]

def _validate(inputs: ReturnFlowInputs) -> None:
    if inputs.incoming_power_density_w_m3 < 0:
        raise ValueError("incoming power density cannot be negative")
    if not D(0) <= inputs.active_volume_fraction <= D(1):
        raise ValueError("active_volume_fraction must be in [0, 1]")
    if not D(0) <= inputs.return_probability <= D(1):
        raise ValueError("return_probability must be in [0, 1]")
    if not D(0) <= inputs.return_efficiency <= D(1):
        raise ValueError("return_efficiency must be in [0, 1]")
    if inputs.reference_power_density_w_m3 <= 0:
        raise ValueError("reference_power_density_w_m3 must be positive")

def return_fraction(normalized_load: Decimal, model_name: ModelName, coefficient: Decimal, *, exponent: Decimal = D("1"), maximum_fraction: Decimal = D("1")) -> Decimal:
    """Evaluate a bounded candidate response curve."""
    if normalized_load < 0 or coefficient < 0:
        raise ValueError("load and coefficient must be non-negative")
    if not D(0) < maximum_fraction <= D(1):
        raise ValueError("maximum_fraction must be in (0, 1]")
    if model_name == "linear":
        return min(maximum_fraction, coefficient * normalized_load)
    if model_name == "power":
        if exponent <= 0:
            raise ValueError("power exponent must be positive")
        return min(maximum_fraction, coefficient * (normalized_load ** exponent))
    if model_name == "saturating":
        return maximum_fraction * (D(1) - (-coefficient * normalized_load).exp())
    raise ValueError("unknown return-flow model: " + str(model_name))

def calculate_return_flow(inputs: ReturnFlowInputs, *, model_name: ModelName = "linear", coefficient: Decimal = D("1"), exponent: Decimal = D("1"), maximum_fraction: Decimal = D("1")) -> ReturnFlowResult:
    """Calculate returned and retained power density for a selected curve."""
    _validate(inputs)
    load = inputs.incoming_power_density_w_m3 / inputs.reference_power_density_w_m3
    curve = return_fraction(load, model_name, coefficient, exponent=exponent, maximum_fraction=maximum_fraction)
    channel = inputs.active_volume_fraction * inputs.return_probability * inputs.return_efficiency
    fraction = min(D(1), channel * curve)
    returned = inputs.incoming_power_density_w_m3 * fraction
    return ReturnFlowResult(load, fraction, returned, inputs.incoming_power_density_w_m3 - returned, model_name, {
        "response_curve": "FITTED" if model_name != "linear" else "ASSUMED_OR_FITTED",
        "coefficient": "FITTED_OR_USER_SUPPLIED",
        "exponent": "FITTED_OR_USER_SUPPLIED" if model_name == "power" else "NOT_APPLICABLE",
        "maximum_fraction": "ASSUMED_OR_USER_SUPPLIED",
        "channel_multiplier": "USER_SUPPLIED",
    })

def dynamic_relaxation(previous_fraction: float, target_fraction: float, elapsed_s: float, time_constant_s: float) -> float:
    """First-order delayed response toward a target return fraction."""
    if not 0.0 <= previous_fraction <= 1.0 or not 0.0 <= target_fraction <= 1.0:
        raise ValueError("fractions must be in [0, 1]")
    if elapsed_s < 0.0 or time_constant_s <= 0.0:
        raise ValueError("elapsed_s must be non-negative and time_constant_s positive")
    return target_fraction + (previous_fraction - target_fraction) * exp(-elapsed_s / time_constant_s)
