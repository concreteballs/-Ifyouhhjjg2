"""Deterministic weighted fitting for candidate redshift response curves."""
from __future__ import annotations
from dataclasses import dataclass
from itertools import product
from math import exp, isfinite, sqrt
from typing import Iterable
from .model import RedshiftObservation

@dataclass(frozen=True)
class RedshiftFit:
    model_name: str
    parameters: dict[str, float]
    weighted_rmse: float
    chi_squared: float
    score: float
    observation_count: int
    input_kind: str
    status: str
    sufficiency: str

def _predict(name: str, x: float, params: dict[str, float]) -> float:
    sign, magnitude = (1.0 if x >= 0 else -1.0), abs(x)
    if name == "linear":
        return params["coefficient"] * x
    if name == "power":
        return params["coefficient"] * sign * (magnitude ** params["exponent"])
    if name == "saturating":
        return sign * params["cap"] * (1.0 - exp(-params["rate"] * magnitude))
    raise ValueError("unknown model: " + name)

def fit_redshift_models(observations: Iterable[RedshiftObservation], *,
    input_scale: float = 1e-18, output_scale: float = 1e-18,
    coefficient_grid: tuple[float, ...] = (0.5, 0.75, 1.0, 1.05, 1.064, 1.1, 1.25, 1.5),
    exponent_grid: tuple[float, ...] = (0.75, 0.9, 1.0, 1.1, 1.25),
    saturation_rate_grid: tuple[float, ...] = (0.0001, 0.0002, 0.00022, 0.00025, 0.0005),
    saturation_cap_grid: tuple[float, ...] = (5000.0, 5130.0, 5500.0, 10000.0),
    complexity_penalty: float = 1.0) -> list[RedshiftFit]:
    """Grid fit with uncertainty-weighted chi-square and complexity penalty."""
    data = tuple(observations)
    if len(data) < 2:
        raise ValueError("at least two observations are required")
    kinds = {item.input_kind for item in data}
    if len(kinds) != 1:
        raise ValueError("all observations must use the same input_kind")
    for value, label in ((input_scale, "input_scale"), (output_scale, "output_scale"), (complexity_penalty, "complexity_penalty")):
        if not isfinite(value):
            raise ValueError(label + " must be finite")
    if input_scale <= 0 or output_scale <= 0 or complexity_penalty < 0:
        raise ValueError("scales must be positive and penalty non-negative")
    for item in data:
        for value, label in ((item.x, "x"), (item.y, "y"), (item.sigma, "sigma")):
            if not isfinite(value):
                raise ValueError(label + " must be finite")
        if item.sigma <= 0:
            raise ValueError("every observation sigma must be positive")
    scaled = tuple((item.x / input_scale, item.y / output_scale, item.sigma / output_scale) for item in data)
    specs = [
        ("linear", (("coefficient", coefficient_grid),)),
        ("power", (("coefficient", coefficient_grid), ("exponent", exponent_grid))),
        ("saturating", (("rate", saturation_rate_grid), ("cap", saturation_cap_grid))),
    ]
    results = []
    for name, dimensions in specs:
        keys, grids = [d[0] for d in dimensions], [d[1] for d in dimensions]
        if any(not grid for grid in grids):
            raise ValueError("parameter grids cannot be empty")
        for values in product(*grids):
            params = dict(zip(keys, values))
            if any(not isfinite(v) or v <= 0 for v in values):
                raise ValueError("all grid parameters must be finite and positive")
            residuals = [(_predict(name, x, params) - y) / sigma for x, y, sigma in scaled]
            chi2 = sum(v * v for v in residuals)
            results.append(RedshiftFit(
                name, params, sqrt(chi2 / len(data)), chi2,
                chi2 + complexity_penalty * len(params), len(data),
                next(iter(kinds)), "FITTED",
                "UNDERDETERMINED" if len(data) < 3 else "EXPLORATORY",
            ))
    return sorted(results, key=lambda item: (item.score, item.model_name, tuple(sorted(item.parameters.items()))))
