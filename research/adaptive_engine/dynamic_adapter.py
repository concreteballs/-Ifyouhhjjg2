"""Adaptive temporal fitting for TIK return-flow states."""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite, sqrt
from typing import Iterable

from research.return_flow.model import dynamic_relaxation
from research.tik0.local_state import TIKLocalStateInputs, calculate_local_state


@dataclass(frozen=True)
class TIKTimeObservation:
    observation_id: str
    time_s: float
    state: TIKLocalStateInputs
    observed_return_fraction: float
    weight: float = 1.0


@dataclass(frozen=True)
class DynamicTIKCandidate:
    return_model: str
    return_coefficient: float
    return_exponent: float
    time_constant_s: float
    initial_fraction: float
    rmse: float
    weighted_rmse: float
    observation_count: int


@dataclass(frozen=True)
class DynamicTIKResult:
    selected: DynamicTIKCandidate
    alternatives: tuple[DynamicTIKCandidate, ...]


def _steady_target(item: TIKTimeObservation, model: str,
                   coefficient: float, exponent: float) -> float:
    from decimal import Decimal
    result = calculate_local_state(
        item.state,
        return_model_name=model,
        return_coefficient=Decimal(str(coefficient)),
        return_exponent=Decimal(str(exponent)),
    )
    return float(result.return_flow.return_fraction)


def _predict_series(data: tuple[TIKTimeObservation, ...], model: str,
                    coefficient: float, exponent: float, tau: float,
                    initial: float) -> tuple[float, ...]:
    previous = initial
    previous_time = data[0].time_s
    predictions = []
    for index, item in enumerate(data):
        target = _steady_target(item, model, coefficient, exponent)
        elapsed = 0.0 if index == 0 else item.time_s - previous_time
        previous = dynamic_relaxation(previous, target, elapsed, tau)
        predictions.append(previous)
        previous_time = item.time_s
    return tuple(predictions)


def fit_dynamic_tik_series(
    observations: Iterable[TIKTimeObservation],
    *,
    return_models: tuple[str, ...] = ("linear", "power", "saturating"),
    return_coefficients: tuple[float, ...] = (0.1, 0.5, 1.0, 2.0),
    return_exponents: tuple[float, ...] = (0.75, 1.0, 1.5),
    time_constants_s: tuple[float, ...] = (0.1, 0.5, 1.0, 2.0, 5.0, 10.0),
    initial_fractions: tuple[float, ...] = (0.0, 0.1, 0.25, 0.5, 1.0),
) -> DynamicTIKResult:
    """Jointly fit return response and relaxation time to a TIK time series."""
    data = tuple(observations)
    if len(data) < 2:
        raise ValueError("at least two time observations are required")
    if len({item.observation_id for item in data}) != len(data):
        raise ValueError("observation_id values must be unique")
    if any(not item.observation_id.strip() for item in data):
        raise ValueError("observation_id is required")
    if any(not all(isfinite(v) for v in (
        item.time_s, item.observed_return_fraction, item.weight
    )) or not 0.0 <= item.observed_return_fraction <= 1.0 or item.weight <= 0
        for item in data):
        raise ValueError("times and weights must be finite; fractions in [0, 1]; weights positive")
    if any(data[i].time_s <= data[i - 1].time_s for i in range(1, len(data))):
        raise ValueError("time_s values must be strictly increasing")
    if not return_models or any(v not in ("linear", "power", "saturating") for v in return_models):
        raise ValueError("unsupported return model")
    for grid, label in (
        (return_coefficients, "return_coefficients"),
        (time_constants_s, "time_constants_s"),
    ):
        if not grid or any(not isfinite(v) or v <= 0 for v in grid):
            raise ValueError(label + " must contain finite positive values")
    if not return_exponents or any(not isfinite(v) or v <= 0 for v in return_exponents):
        raise ValueError("return_exponents must contain finite positive values")
    if not initial_fractions or any(not isfinite(v) or not 0 <= v <= 1 for v in initial_fractions):
        raise ValueError("initial_fractions must lie in [0, 1]")

    candidates = []
    total_weight = sum(item.weight for item in data)
    for model in return_models:
        exponents = return_exponents if model == "power" else (1.0,)
        for coefficient in return_coefficients:
            for exponent in exponents:
                for tau in time_constants_s:
                    for initial in initial_fractions:
                        predicted = _predict_series(data, model, coefficient, exponent, tau, initial)
                        squared = sum(
                            item.weight * (guess - item.observed_return_fraction) ** 2
                            for item, guess in zip(data, predicted)
                        )
                        weighted_rmse = sqrt(squared / total_weight)
                        rmse = sqrt(sum(
                            (guess - item.observed_return_fraction) ** 2
                            for item, guess in zip(data, predicted)
                        ) / len(data))
                        candidates.append(DynamicTIKCandidate(
                            model, coefficient, exponent, tau, initial,
                            rmse, weighted_rmse, len(data),
                        ))
    candidates.sort(key=lambda item: (
        item.weighted_rmse, item.rmse, item.return_model,
        item.return_coefficient, item.return_exponent,
        item.time_constant_s, item.initial_fraction,
    ))
    return DynamicTIKResult(candidates[0], tuple(candidates[1:]))
