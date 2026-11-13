"""Bounded search over explicitly selected raw TIK-0 inputs."""
from __future__ import annotations
from dataclasses import dataclass, replace
from decimal import Decimal, InvalidOperation
from itertools import product
from math import prod
from typing import Iterable
from research.tik0.local_state import TIKLocalStateInputs
from .tik_adapter import TIKAdaptiveResult, TIKPairObservation, fit_tik_pairs

D = Decimal
RAW_PARAMETERS = frozenset({
    "observation_volume_m3", "active_cell_count", "cell_volume_m3",
    "transmission_probability", "event_energy_j",
    "return_channel_coverage_fraction", "return_probability",
    "return_efficiency", "return_reference_power_density_w_m3",
})

@dataclass(frozen=True)
class TIKRawParameterGrid:
    """Candidate values for one field on one side of one named observation."""
    observation_id: str
    side: str
    parameter: str
    values: tuple[float | int | Decimal, ...]

@dataclass(frozen=True)
class TIKRawSearchCandidate:
    parameter_values: tuple[tuple[str, str, str, str], ...]
    fit: TIKAdaptiveResult
    score: float

@dataclass(frozen=True)
class TIKRawSearchResult:
    selected: TIKRawSearchCandidate
    alternatives: tuple[TIKRawSearchCandidate, ...]
    attempted_count: int
    rejected_count: int
    valid_count: int

def _decimal(value: float | int | Decimal, label: str) -> Decimal:
    if isinstance(value, bool):
        raise ValueError(label + " values must be numeric, not boolean")
    try:
        result = D(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError(label + " values must be finite numbers") from None
    if not result.is_finite():
        raise ValueError(label + " values must be finite numbers")
    return result

def _normalize_grids(grids, observations, *, max_dimensions, max_candidates):
    raw = tuple(grids)
    if not raw:
        raise ValueError("at least one raw parameter grid is required")
    if len(raw) > max_dimensions:
        raise ValueError("raw parameter dimensions exceed max_dimensions")
    ids = {item.observation_id for item in observations}
    seen, normalized = set(), []
    for grid in raw:
        if grid.observation_id not in ids:
            raise ValueError("unknown observation_id in raw parameter grid: " + grid.observation_id)
        if grid.side not in ("state_a", "state_b"):
            raise ValueError("side must be state_a or state_b")
        if grid.parameter not in RAW_PARAMETERS:
            raise ValueError("unsupported raw TIK parameter: " + grid.parameter)
        key = (grid.observation_id, grid.side, grid.parameter)
        if key in seen:
            raise ValueError("each raw parameter target may have only one grid")
        seen.add(key)
        if not grid.values:
            raise ValueError("raw parameter grids cannot be empty")
        values = []
        for value in grid.values:
            number = _decimal(value, grid.parameter)
            if grid.parameter == "active_cell_count":
                if number != number.to_integral_value() or number < 1:
                    raise ValueError("active_cell_count candidates must be positive integers")
                normalized_value = int(number)
            else:
                normalized_value = number
            if normalized_value not in values:
                values.append(normalized_value)
        normalized.append((grid, tuple(values)))
    count = prod(len(values) for _, values in normalized)
    if count > max_candidates:
        raise ValueError("raw parameter search has " + str(count)
            + " combinations; max_candidates is " + str(max_candidates))
    return tuple(normalized)

def _replace_state(state: TIKLocalStateInputs, parameter: str, value):
    if parameter in {"observation_volume_m3", "active_cell_count",
                     "cell_volume_m3", "transmission_probability", "event_energy_j"}:
        tik_value = value if parameter == "active_cell_count" else D(value)
        return replace(state, tik=replace(state.tik, **{parameter: tik_value}))
    return replace(state, **{parameter: D(value)})

def _apply_values(observations, grids, values):
    by_id = {item.observation_id: item for item in observations}
    for (grid, _), value in zip(grids, values):
        item = by_id[grid.observation_id]
        if grid.side == "state_a":
            by_id[grid.observation_id] = replace(
                item, state_a=_replace_state(item.state_a, grid.parameter, value))
        else:
            by_id[grid.observation_id] = replace(
                item, state_b=_replace_state(item.state_b, grid.parameter, value))
    return tuple(by_id[item.observation_id] for item in observations)

def fit_tik_raw_parameters(
    observations: Iterable[TIKPairObservation],
    raw_parameter_grids: Iterable[TIKRawParameterGrid],
    *,
    max_dimensions: int = 4,
    max_candidates: int = 256,
    return_models: tuple[str, ...] = ("linear", "power", "saturating"),
    return_coefficients: tuple[float, ...] = (0.1, 0.5, 1.0, 2.0),
    return_exponents: tuple[float, ...] = (0.75, 1.0, 1.5),
    response_formulas: tuple[str, ...] = ("linear", "power", "saturating"),
    maximum_relative_change: float = 0.1,
) -> TIKRawSearchResult:
    """Search bounded raw inputs and fit the complete TIK -> return -> response chain."""
    data = tuple(observations)
    if len(data) < 2:
        raise ValueError("at least two paired observations are required")
    if max_dimensions < 1 or max_candidates < 1:
        raise ValueError("search limits must be positive integers")
    grids = _normalize_grids(raw_parameter_grids, data,
        max_dimensions=max_dimensions, max_candidates=max_candidates)
    attempted = prod(len(values) for _, values in grids)
    ranked, rejected = [], 0
    for combination in product(*(values for _, values in grids)):
        candidate_data = _apply_values(data, grids, combination)
        try:
            fitted = fit_tik_pairs(candidate_data, return_models=return_models,
                return_coefficients=return_coefficients, return_exponents=return_exponents,
                response_formulas=response_formulas,
                maximum_relative_change=maximum_relative_change)
        except (ValueError, ArithmeticError, OverflowError):
            rejected += 1
            continue
        labels = tuple((grid.observation_id, grid.side, grid.parameter, str(value))
            for (grid, _), value in zip(grids, combination))
        ranked.append(TIKRawSearchCandidate(labels, fitted, fitted.selected.score))
    if not ranked:
        raise ValueError("all raw TIK candidates were invalid ("
            + str(rejected) + " of " + str(attempted) + " rejected)")
    ranked.sort(key=lambda item: (item.score,
        item.fit.selected.response.weighted_rmse, item.parameter_values,
        item.fit.selected.return_model, item.fit.selected.return_coefficient,
        item.fit.selected.response.formula))
    return TIKRawSearchResult(ranked[0], tuple(ranked[1:]),
        attempted, rejected, len(ranked))
