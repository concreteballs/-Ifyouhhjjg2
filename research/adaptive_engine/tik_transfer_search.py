"""Component-level transfer hints and bounded TIK parameter recombination.

Transfer proposals are hypotheses, not evidence of model quality. Only FIT rows
are optimized; independent HOLDOUT rows are evaluated after parameters freeze.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from math import isfinite, prod
from typing import Iterable

from research.tik0.local_state import TIKLocalStateInputs
from .raw_parameter_search import (
    RAW_PARAMETERS, TIKRawParameterGrid, fit_tik_raw_parameters,
)
from .tik_adapter import TIKAdaptiveResult, TIKPairObservation, _paired_contrast
from .formulas import predict
from .tik_research_pipeline import TIKResearchObservation, TIKResearchResult, TIKHoldoutReport, TIKHoldoutPrediction


@dataclass(frozen=True)
class TIKTransferRule:
    """Explicitly maps one reusable component to a target raw TIK parameter."""
    rule_id: str
    component: str
    source_parameter: str
    target_parameter: str
    source_side: str = "state_a"
    target_side: str = "state_a"
    multipliers: tuple[float, ...] = (1.0,)
    offsets: tuple[float, ...] = (0.0,)

    def __post_init__(self):
        if not self.rule_id.strip() or not self.component.strip():
            raise ValueError("rule_id and component are required")
        if self.source_parameter not in RAW_PARAMETERS or self.target_parameter not in RAW_PARAMETERS:
            raise ValueError("transfer rule uses an unsupported raw TIK parameter")
        if self.source_side not in ("state_a", "state_b") or self.target_side not in ("state_a", "state_b"):
            raise ValueError("transfer sides must be state_a or state_b")
        if not self.multipliers or not self.offsets:
            raise ValueError("transfer transformations cannot be empty")
        if any(not isfinite(v) for v in self.multipliers + self.offsets):
            raise ValueError("transfer transformations must be finite")


@dataclass(frozen=True)
class TIKComponentHint:
    proposal_id: str
    source_observation_id: str
    source_profile_id: str
    component: str
    target_parameter: str
    target_side: str
    candidate_values: tuple[float, ...]
    rule_id: str
    rationale: str


@dataclass(frozen=True)
class TIKTransferCandidate:
    candidate_id: str
    grids: tuple[TIKRawParameterGrid, ...]
    proposal_ids: tuple[str, ...]


@dataclass(frozen=True)
class TIKTransferEvaluation:
    candidate_id: str
    proposal_ids: tuple[str, ...]
    fit: TIKAdaptiveResult
    holdout: TIKHoldoutReport | None
    score: float


@dataclass(frozen=True)
class TIKTransferSearchResult:
    proposals: tuple[TIKComponentHint, ...]
    candidates: tuple[TIKTransferCandidate, ...]
    evaluations: tuple[TIKTransferEvaluation, ...]
    attempted_count: int
    rejected_count: int


def _read_parameter(state: TIKLocalStateInputs, parameter: str) -> float:
    if parameter in {"observation_volume_m3", "active_cell_count", "cell_volume_m3",
                     "transmission_probability", "event_energy_j"}:
        value = getattr(state.tik, parameter)
    else:
        value = getattr(state, parameter)
    return float(value)


def propose_tik_component_hints(
    partial_observations: Iterable[TIKResearchObservation],
    rules: Iterable[TIKTransferRule],
    *,
    transferable_components: dict[str, tuple[str, ...]],
) -> tuple[TIKComponentHint, ...]:
    """Extract explicit component-scoped hints from PARTIAL_TRANSFER sources.

    The caller supplies the already-classified component list per observation.
    No partial observation is fitted or scored by this function.
    """
    data, rule_set = tuple(partial_observations), tuple(rules)
    if len({rule.rule_id for rule in rule_set}) != len(rule_set):
        raise ValueError("transfer rule IDs must be unique")
    proposals = []
    for item in sorted(data, key=lambda value: value.pair.observation_id):
        components = set(transferable_components.get(item.pair.observation_id, ()))
        for rule in sorted(rule_set, key=lambda value: value.rule_id):
            if rule.component not in components:
                continue
            source_state = getattr(item.pair, rule.source_side)
            source_value = _read_parameter(source_state, rule.source_parameter)
            values = tuple(sorted({source_value * multiplier + offset
                                   for multiplier in rule.multipliers
                                   for offset in rule.offsets}))
            if not all(isfinite(value) for value in values):
                continue
            proposals.append(TIKComponentHint(
                "hint:" + item.pair.observation_id + ":" + rule.rule_id,
                item.pair.observation_id, item.profile.profile_id, rule.component,
                rule.target_parameter, rule.target_side, values, rule.rule_id,
                "Transferred only the declared component through the named parameter mapping and transformations.",
            ))
    return tuple(proposals)


def combine_tik_transfer_hints(
    proposals: Iterable[TIKComponentHint],
    fit_observation_ids: Iterable[str],
    *,
    max_candidates: int = 128,
) -> tuple[TIKTransferCandidate, ...]:
    """Combine hints into deterministic, deduplicated bounded raw-parameter grids."""
    if max_candidates < 1:
        raise ValueError("max_candidates must be positive")
    fit_ids = tuple(sorted(set(fit_observation_ids)))
    if not fit_ids:
        raise ValueError("at least one FIT observation ID is required")
    hints = tuple(proposals)
    if not hints:
        return ()
    # Merge independent analogues' values for the same target dimension.
    merged: dict[tuple[str, str], set[float]] = {}
    sources: dict[tuple[str, str], set[str]] = {}
    for hint in hints:
        if hint.target_parameter not in RAW_PARAMETERS or hint.target_side not in ("state_a", "state_b"):
            continue
        key = (hint.target_side, hint.target_parameter)
        merged.setdefault(key, set()).update(hint.candidate_values)
        sources.setdefault(key, set()).add(hint.proposal_id)
    dimensions = sorted((key, tuple(sorted(values))) for key, values in merged.items() if values)
    if not dimensions:
        return ()
    count = prod(len(values) for _, values in dimensions)
    if count > max_candidates:
        raise ValueError("transfer candidate count " + str(count) +
                         " exceeds max_candidates " + str(max_candidates))
    result, seen = [], set()
    for combination in product(*(values for _, values in dimensions)):
        grids = tuple(
            TIKRawParameterGrid(observation_id, side, parameter, (value,))
            for observation_id in fit_ids
            for ((side, parameter), _), value in zip(dimensions, combination)
        )
        signature = tuple((grid.observation_id, grid.side, grid.parameter, str(grid.values[0]))
                          for grid in grids)
        if signature in seen:
            continue
        seen.add(signature)
        used = tuple(sorted({pid for (key, _), _value in zip(dimensions, combination)
                             for pid in sources[key]}))
        result.append(TIKTransferCandidate("transfer:" + str(len(result) + 1), grids, used))
    return tuple(result)


def _score_holdout(fit: TIKAdaptiveResult, observations: tuple[TIKPairObservation, ...]):
    if not observations:
        return None
    selected = fit.selected
    rows, squared, weighted, total = [], 0.0, 0.0, 0.0
    for item in observations:
        x = _paired_contrast(item, selected.return_model,
                             selected.return_coefficient, selected.return_exponent)
        predicted = predict(selected.response.formula, x, selected.response.parameters)
        error = predicted - item.observed_delta
        rows.append(TIKHoldoutPrediction(item.observation_id, item.observed_delta,
                                         predicted, abs(error), item.weight))
        squared += error * error
        weighted += item.weight * error * error
        total += item.weight
    from math import sqrt
    return TIKHoldoutReport(tuple(rows), sqrt(squared / len(rows)),
                            sqrt(weighted / total), len(rows))


def search_tik_transfer_candidates(
    observations: Iterable[TIKResearchObservation],
    research_result: TIKResearchResult,
    rules: Iterable[TIKTransferRule],
    *,
    max_candidates: int = 128,
    return_models: tuple[str, ...] = ("linear", "power", "saturating"),
    return_coefficients: tuple[float, ...] = (0.1, 0.5, 1.0, 2.0),
    return_exponents: tuple[float, ...] = (0.75, 1.0, 1.5),
    response_formulas: tuple[str, ...] = ("linear", "power", "saturating"),
    maximum_relative_change: float = 0.1,
) -> TIKTransferSearchResult:
    """Generate from partial analogues, optimize FIT only, score frozen HOLDOUT."""
    data = tuple(observations)
    by_id = {item.pair.observation_id: item for item in data}
    if len(by_id) != len(data):
        raise ValueError("TIK observation IDs must be unique")
    required_ids = set(research_result.fit_observation_ids) | set(research_result.holdout_observation_ids) | set(research_result.partial_transfer_observation_ids)
    missing_ids = required_ids - set(by_id)
    if missing_ids:
        raise ValueError("research result references observations not supplied: " + ", ".join(sorted(missing_ids)))
    role_by_id = {role.observation_id: role for role in research_result.roles}
    partial = tuple(by_id[key] for key in research_result.partial_transfer_observation_ids
                    if key in by_id and role_by_id.get(key) is not None
                    and role_by_id[key].role.value == "PARTIAL_TRANSFER")
    components = {key: role_by_id[key].assessment.transferable_components for key in
                  research_result.partial_transfer_observation_ids if key in role_by_id}
    proposals = propose_tik_component_hints(partial, rules, transferable_components=components)
    candidates = combine_tik_transfer_hints(proposals, research_result.fit_observation_ids,
                                             max_candidates=max_candidates)
    fit_data = tuple(by_id[key].pair for key in research_result.fit_observation_ids)
    holdout_data = tuple(by_id[key].pair for key in research_result.holdout_observation_ids)
    evaluations, rejected = [], 0
    for candidate in candidates:
        try:
            raw = fit_tik_raw_parameters(
                fit_data, candidate.grids, max_dimensions=len(candidate.grids),
                max_candidates=1, return_models=return_models,
                return_coefficients=return_coefficients, return_exponents=return_exponents,
                response_formulas=response_formulas,
                maximum_relative_change=maximum_relative_change,
            )
        except (ValueError, ArithmeticError, OverflowError):
            rejected += 1
            continue
        fitted = raw.selected.fit
        holdout = _score_holdout(fitted, holdout_data)
        score = (holdout.weighted_rmse + (1e6 if not fitted.selected.stability.passed else 0.0)
                 if holdout is not None else fitted.selected.score)
        evaluations.append(TIKTransferEvaluation(candidate.candidate_id,
            candidate.proposal_ids, fitted, holdout, score))
    evaluations.sort(key=lambda item: (item.score, item.candidate_id))
    return TIKTransferSearchResult(proposals, candidates, tuple(evaluations),
                                   len(candidates), rejected)
