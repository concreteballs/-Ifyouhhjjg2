"""Build a complete TIK-0 and return-channel state for one location."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from research.return_flow.model import ReturnFlowInputs, ReturnFlowResult, calculate_return_flow
from .model import ModelInputs, ModelResult, calculate

D = Decimal


@dataclass(frozen=True)
class TIKLocalStateInputs:
    """All independently declared inputs needed at one clock location.

    return_channel_coverage_fraction describes coverage of the RETURN channel.
    It is deliberately separate from TIK's active-cell volume fraction, which
    has already scaled incoming power density in calculate(ModelInputs).
    """

    tik: ModelInputs
    return_channel_coverage_fraction: Decimal
    return_probability: Decimal
    return_efficiency: Decimal
    return_reference_power_density_w_m3: Decimal


@dataclass(frozen=True)
class TIKLocalStateResult:
    tik: ModelResult
    return_flow: ReturnFlowResult
    parameter_status: dict[str, str]

    def as_dict(self) -> dict[str, Any]:
        return {
            "tik": self.tik.as_dict(),
            "return_flow": {
                "normalized_load": str(self.return_flow.normalized_load),
                "return_fraction": str(self.return_flow.return_fraction),
                "returned_power_density_w_m3": str(self.return_flow.returned_power_density_w_m3),
                "retained_power_density_w_m3": str(self.return_flow.retained_power_density_w_m3),
                "model_name": self.return_flow.model_name,
                "parameter_status": dict(self.return_flow.parameter_status),
            },
            "parameter_status": dict(self.parameter_status),
        }


def calculate_local_state(
    inputs: TIKLocalStateInputs,
    *,
    return_model_name: str = "linear",
    return_coefficient: Decimal = D("1"),
    return_exponent: Decimal = D("1"),
    return_maximum_fraction: Decimal = D("1"),
) -> TIKLocalStateResult:
    """Calculate TIK incoming power, then the local returned/retained flow."""
    if not D(0) <= inputs.return_channel_coverage_fraction <= D(1):
        raise ValueError("return_channel_coverage_fraction must be in [0, 1]")
    if not D(0) <= inputs.return_probability <= D(1):
        raise ValueError("return_probability must be in [0, 1]")
    if not D(0) <= inputs.return_efficiency <= D(1):
        raise ValueError("return_efficiency must be in [0, 1]")
    if inputs.return_reference_power_density_w_m3 <= 0:
        raise ValueError("return_reference_power_density_w_m3 must be positive")
    if inputs.tik.event_energy_j is None:
        raise ValueError("tik.event_energy_j is required to calculate return flow")

    tik_result = calculate(inputs.tik)
    if tik_result.power_density_w_m3 is None:
        raise ValueError("TIK incoming power density is unavailable")

    # TIK active-volume fraction is already included in tik_result.power_density.
    # This independent coverage value applies only to the return channel.
    flow_inputs = ReturnFlowInputs(
        incoming_power_density_w_m3=tik_result.power_density_w_m3,
        active_volume_fraction=inputs.return_channel_coverage_fraction,
        return_probability=inputs.return_probability,
        return_efficiency=inputs.return_efficiency,
        reference_power_density_w_m3=inputs.return_reference_power_density_w_m3,
    )
    flow_result = calculate_return_flow(
        flow_inputs,
        model_name=return_model_name,
        coefficient=return_coefficient,
        exponent=return_exponent,
        maximum_fraction=return_maximum_fraction,
    )
    status = dict(tik_result.parameter_status)
    status.update({
        "return_channel_coverage_fraction": "ASSUMED_OR_USER_SUPPLIED",
        "return_probability": "ASSUMED_OR_USER_SUPPLIED",
        "return_efficiency": "ASSUMED_OR_USER_SUPPLIED",
        "return_reference_power_density_w_m3": "ASSUMED_OR_USER_SUPPLIED",
        "return_response_curve": "ASSUMED_OR_FITTED",
        "return_coefficient": "ASSUMED_OR_FITTED",
        "return_exponent": "ASSUMED_OR_FITTED" if return_model_name == "power" else "NOT_APPLICABLE",
        "return_maximum_fraction": "ASSUMED_OR_USER_SUPPLIED",
        "active_volume_fraction_applied_once": "DERIVED",
    })
    return TIKLocalStateResult(tik_result, flow_result, status)
