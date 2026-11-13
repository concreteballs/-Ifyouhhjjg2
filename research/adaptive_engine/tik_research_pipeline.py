"""Applicability-aware TIK fitting with leakage-safe independent evaluation."""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite, sqrt
from typing import Iterable

from .formulas import predict
from .tik_adapter import TIKAdaptiveResult, TIKPairObservation, _paired_contrast, fit_tik_pairs
from .transfer_engine import (
    DatasetObservation, DatasetRole, ObservationRole, ProcessProfile,
    build_applicability_split,
)


@dataclass(frozen=True)
class TIKResearchObservation:
    pair: TIKPairObservation
    group_id: str
    profile: ProcessProfile


@dataclass(frozen=True)
class TIKHoldoutPrediction:
    observation_id: str
    observed_delta: float
    predicted_delta: float
    absolute_error: float
    weight: float


@dataclass(frozen=True)
class TIKHoldoutReport:
    predictions: tuple[TIKHoldoutPrediction, ...]
    rmse: float
    weighted_rmse: float
    observation_count: int


@dataclass(frozen=True)
class TIKResearchResult:
    fit: TIKAdaptiveResult
    roles: tuple[ObservationRole, ...]
    holdout: TIKHoldoutReport | None
    fit_observation_ids: tuple[str, ...]
    holdout_observation_ids: tuple[str, ...]
    partial_transfer_observation_ids: tuple[str, ...]
    adaptation_observation_ids: tuple[str, ...]
    excluded_observation_ids: tuple[str, ...]
    unresolved_observation_ids: tuple[str, ...]


def _evaluate_holdout(fit: TIKAdaptiveResult,
                      observations: tuple[TIKPairObservation, ...]) -> TIKHoldoutReport | None:
    if not observations:
        return None
    selected = fit.selected
    predictions = []
    weighted_error = total_weight = squared_error = 0.0
    for item in observations:
        x = _paired_contrast(item, selected.return_model,
                             selected.return_coefficient, selected.return_exponent)
        predicted = predict(selected.response.formula, x, selected.response.parameters)
        error = predicted - item.observed_delta
        predictions.append(TIKHoldoutPrediction(
            item.observation_id, item.observed_delta, predicted, abs(error), item.weight
        ))
        squared_error += error * error
        weighted_error += item.weight * error * error
        total_weight += item.weight
    return TIKHoldoutReport(
        tuple(predictions), sqrt(squared_error / len(predictions)),
        sqrt(weighted_error / total_weight), len(predictions)
    )


def fit_tik_research_dataset(
    observations: Iterable[TIKResearchObservation],
    *,
    reference_profile: ProcessProfile,
    fit_group_ids: Iterable[str],
    holdout_group_ids: Iterable[str],
    model_family: str = "TIK-0-paired-response",
    return_models: tuple[str, ...] = ("linear", "power", "saturating"),
    return_coefficients: tuple[float, ...] = (0.1, 0.5, 1.0, 2.0),
    return_exponents: tuple[float, ...] = (0.75, 1.0, 1.5),
    response_formulas: tuple[str, ...] = ("linear", "power", "saturating"),
    maximum_relative_change: float = 0.1,
) -> TIKResearchResult:
    """Classify first, fit FIT observations only, then evaluate untouched HOLDOUT.

    Partial analogues remain available as component-transfer material but are
    never silently promoted into fitting or direct holdout scoring.
    """
    data = tuple(observations)
    if len({item.pair.observation_id for item in data}) != len(data):
        raise ValueError("TIK observation IDs must be unique")
    if any(not item.group_id.strip() for item in data):
        raise ValueError("every TIK observation requires a group_id")

    roles = build_applicability_split(
        reference_profile,
        (DatasetObservation(item.pair.observation_id, item.group_id, item.profile)
         for item in data),
        fit_group_ids=fit_group_ids,
        holdout_group_ids=holdout_group_ids,
        model_family=model_family,
    )
    role_by_id = {item.observation_id: item.role for item in roles}
    pairs_by_id = {item.pair.observation_id: item.pair for item in data}

    fit_ids = tuple(sorted(key for key, role in role_by_id.items()
                           if role == DatasetRole.FIT))
    holdout_ids = tuple(sorted(key for key, role in role_by_id.items()
                               if role == DatasetRole.HOLDOUT))
    partial_ids = tuple(sorted(key for key, role in role_by_id.items()
                               if role == DatasetRole.PARTIAL_TRANSFER))
    adaptation_ids = tuple(sorted(key for key, role in role_by_id.items()
                                  if role == DatasetRole.ADAPTATION_REQUIRED))
    excluded_ids = tuple(sorted(key for key, role in role_by_id.items()
                                if role == DatasetRole.EXCLUDED))
    unresolved_ids = tuple(sorted(key for key, role in role_by_id.items()
                                  if role == DatasetRole.UNRESOLVED))

    if len(fit_ids) < 2:
        raise ValueError("at least two independently grouped FIT observations are required")
    fit_data = tuple(pairs_by_id[key] for key in fit_ids)
    fitted = fit_tik_pairs(
        fit_data, return_models=return_models,
        return_coefficients=return_coefficients,
        return_exponents=return_exponents,
        response_formulas=response_formulas,
        maximum_relative_change=maximum_relative_change,
    )
    holdout_data = tuple(pairs_by_id[key] for key in holdout_ids)
    holdout_report = _evaluate_holdout(fitted, holdout_data)

    return TIKResearchResult(
        fitted, roles, holdout_report, fit_ids, holdout_ids,
        partial_ids, adaptation_ids, excluded_ids, unresolved_ids
    )
