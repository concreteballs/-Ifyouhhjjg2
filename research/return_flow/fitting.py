"""Deterministic grid fitting and ranking for return-flow candidate models."""
from __future__ import annotations
from dataclasses import dataclass
from itertools import product
from math import exp, sqrt
from typing import Iterable
from .model import dynamic_relaxation

@dataclass(frozen=True)
class FitObservation:
    normalized_load: float
    observed_return_fraction: float
    elapsed_s: float | None = None

@dataclass(frozen=True)
class ModelFit:
    model_name: str
    parameters: dict[str, float]
    rmse: float
    penalized_score: float
    observation_count: int
    status: str = "FITTED"

def _validate_observations(observations: tuple[FitObservation, ...]) -> None:
    if len(observations) < 2:
        raise ValueError("at least two observations are required")
    previous_time = None
    for item in observations:
        if item.normalized_load < 0:
            raise ValueError("normalized_load cannot be negative")
        if not 0.0 <= item.observed_return_fraction <= 1.0:
            raise ValueError("observed return fraction must be in [0, 1]")
        if item.elapsed_s is not None:
            if item.elapsed_s < 0:
                raise ValueError("elapsed_s cannot be negative")
            if previous_time is not None and item.elapsed_s < previous_time:
                raise ValueError("elapsed_s values must be non-decreasing")
            previous_time = item.elapsed_s

def _predict(name: str, observations: tuple[FitObservation, ...], params: dict[str, float], cap: float) -> list[float]:
    predictions, state, previous_time = [], 0.0, None
    for item in observations:
        x = item.normalized_load
        if name == "linear":
            value = min(cap, params["coefficient"] * x)
        elif name == "power":
            value = min(cap, params["coefficient"] * (x ** params["exponent"]))
        elif name == "saturating":
            value = cap * (1.0 - exp(-params["coefficient"] * x))
        elif name == "dynamic_saturating":
            if item.elapsed_s is None:
                raise ValueError("dynamic_saturating requires elapsed_s on every observation")
            target = cap * (1.0 - exp(-params["coefficient"] * x))
            dt = 0.0 if previous_time is None else item.elapsed_s - previous_time
            state = dynamic_relaxation(state, target, dt, params["time_constant_s"])
            value, previous_time = state, item.elapsed_s
        else:
            raise ValueError("unknown model: " + name)
        predictions.append(value)
    return predictions

def fit_models(observations: Iterable[FitObservation], *, maximum_fraction: float = 1.0, coefficient_grid: tuple[float, ...] = (0.1, 0.25, 0.5, 1.0, 2.0, 4.0), exponent_grid: tuple[float, ...] = (0.5, 1.0, 1.5, 2.0), time_constant_grid_s: tuple[float, ...] = (0.1, 1.0, 10.0), complexity_penalty: float = 0.0) -> list[ModelFit]:
    """Fit candidate curves by deterministic grid search, best first."""
    data = tuple(observations)
    _validate_observations(data)
    if not 0.0 < maximum_fraction <= 1.0:
        raise ValueError("maximum_fraction must be in (0, 1]")
    if complexity_penalty < 0:
        raise ValueError("complexity_penalty cannot be negative")
    if not coefficient_grid or any(v <= 0 for v in coefficient_grid):
        raise ValueError("coefficient_grid must contain positive values")
    if not exponent_grid or any(v <= 0 for v in exponent_grid):
        raise ValueError("exponent_grid must contain positive values")
    if not time_constant_grid_s or any(v <= 0 for v in time_constant_grid_s):
        raise ValueError("time_constant_grid_s must contain positive values")
    specs = [
        ("linear", (("coefficient", coefficient_grid),)),
        ("power", (("coefficient", coefficient_grid), ("exponent", exponent_grid))),
        ("saturating", (("coefficient", coefficient_grid),)),
        ("dynamic_saturating", (("coefficient", coefficient_grid), ("time_constant_s", time_constant_grid_s))),
    ]
    candidates = []
    for name, dimensions in specs:
        if name == "dynamic_saturating" and any(item.elapsed_s is None for item in data):
            continue
        keys, grids = [d[0] for d in dimensions], [d[1] for d in dimensions]
        for values in product(*grids):
            params = dict(zip(keys, values))
            predicted = _predict(name, data, params, maximum_fraction)
            mse = sum((p - item.observed_return_fraction) ** 2 for p, item in zip(predicted, data)) / len(data)
            rmse = sqrt(mse)
            score = rmse + complexity_penalty * len(params) / len(data)
            candidates.append(ModelFit(name, params, rmse, score, len(data)))
    return sorted(candidates, key=lambda item: (item.penalized_score, item.model_name, tuple(sorted(item.parameters.items()))))
