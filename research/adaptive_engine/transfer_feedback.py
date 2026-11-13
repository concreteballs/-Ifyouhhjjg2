"""Evidence-based feedback and durable history for component transfer candidates.

HOLDOUT observations are read only from frozen reports. This module never
refits candidates and never promotes HOLDOUT rows into FIT.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Iterable

from .tik_research_pipeline import TIKResearchResult
from .tik_transfer_search import TIKTransferSearchResult


@dataclass(frozen=True)
class TransferCandidateFeedback:
    candidate_id: str
    proposal_ids: tuple[str, ...]
    components: tuple[str, ...]
    fit_score: float
    baseline_fit_score: float
    fit_improvement: float
    holdout_score: float | None
    baseline_holdout_score: float | None
    holdout_improvement: float | None
    stable: bool
    holdout_count: int
    outcome: str


@dataclass(frozen=True)
class TransferFeedbackReport:
    baseline_fit_score: float
    baseline_holdout_score: float | None
    evaluations: tuple[TransferCandidateFeedback, ...]
    fit_observation_ids: tuple[str, ...]
    holdout_observation_ids: tuple[str, ...]
    partial_transfer_observation_ids: tuple[str, ...]


def _improvement(baseline: float, candidate: float) -> float:
    """Positive means candidate error/score is lower than baseline."""
    return baseline - candidate


def build_transfer_feedback(
    search: TIKTransferSearchResult,
    baseline: TIKResearchResult,
) -> TransferFeedbackReport:
    """Compare candidates with the original frozen baseline on the same rows."""
    baseline_fit = float(baseline.fit.selected.score)
    baseline_holdout = (float(baseline.holdout.weighted_rmse)
                        if baseline.holdout is not None else None)
    proposals = {item.proposal_id: item for item in search.proposals}
    feedback = []
    for item in search.evaluations:
        stable = bool(item.fit.selected.stability.passed)
        fit_score = float(item.fit.selected.score)
        holdout_score = (float(item.holdout.weighted_rmse)
                         if item.holdout is not None else None)
        fit_gain = _improvement(baseline_fit, fit_score)
        holdout_gain = (_improvement(baseline_holdout, holdout_score)
                        if baseline_holdout is not None and holdout_score is not None
                        else None)
        if not stable:
            outcome = "unstable"
        elif holdout_gain is None:
            outcome = "fit_only_unverified"
        elif holdout_gain > 0:
            outcome = "holdout_improved"
        elif holdout_gain < 0:
            outcome = "holdout_regressed"
        else:
            outcome = "holdout_unchanged"
        feedback.append(TransferCandidateFeedback(
            item.candidate_id, tuple(sorted(item.proposal_ids)),
            tuple(sorted({proposals[p].component for p in item.proposal_ids if p in proposals})),
            fit_score, baseline_fit, fit_gain, holdout_score, baseline_holdout,
            holdout_gain, stable,
            item.holdout.observation_count if item.holdout is not None else 0,
            outcome,
        ))
    feedback.sort(key=lambda row: (
        0 if row.outcome == "holdout_improved" else 1,
        0 if row.stable else 1,
        -(row.holdout_improvement or 0.0), row.candidate_id,
    ))
    return TransferFeedbackReport(
        baseline_fit, baseline_holdout, tuple(feedback),
        tuple(baseline.fit_observation_ids), tuple(baseline.holdout_observation_ids),
        tuple(baseline.partial_transfer_observation_ids),
    )


class TransferFeedbackRegistry:
    """Append-only JSON history; repeated run IDs are rejected, not overwritten."""

    def __init__(self):
        self._runs: dict[str, TransferFeedbackReport] = {}

    def record(self, run_id: str, report: TransferFeedbackReport) -> None:
        if not run_id or not run_id.strip():
            raise ValueError("run_id is required")
        if run_id in self._runs:
            raise ValueError("run_id already exists: " + run_id)
        self._runs[run_id] = report

    def get(self, run_id: str) -> TransferFeedbackReport:
        return self._runs[run_id]

    def run_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._runs))

    def component_statistics(self) -> dict[str, dict[str, int]]:
        stats: dict[str, dict[str, int]] = {}
        for report in self._runs.values():
            for row in report.evaluations:
                for component in row.components:
                    item = stats.setdefault(component, {
                        "evaluations": 0, "holdout_improved": 0,
                        "holdout_regressed": 0, "unstable": 0,
                        "fit_only_unverified": 0,
                    })
                    item["evaluations"] += 1
                    if row.outcome in item:
                        item[row.outcome] += 1
        return {key: stats[key] for key in sorted(stats)}

    def export_json(self, path: str | Path) -> None:
        payload = {
            "schema": "tik-transfer-feedback.v1",
            "runs": {
                run_id: asdict(self._runs[run_id]) for run_id in sorted(self._runs)
            },
        }
        Path(path).write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    def load_json(self, path: str | Path) -> None:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        if payload.get("schema") != "tik-transfer-feedback.v1":
            raise ValueError("unsupported transfer feedback registry schema")
        for run_id, raw in payload.get("runs", {}).items():
            evaluations = tuple(TransferCandidateFeedback(
                row["candidate_id"], tuple(row["proposal_ids"]), tuple(row["components"]),
                row["fit_score"], row["baseline_fit_score"], row["fit_improvement"],
                row["holdout_score"], row["baseline_holdout_score"],
                row["holdout_improvement"], row["stable"], row["holdout_count"],
                row["outcome"],
            ) for row in raw["evaluations"])
            report = TransferFeedbackReport(
                raw["baseline_fit_score"], raw["baseline_holdout_score"], evaluations,
                tuple(raw["fit_observation_ids"]), tuple(raw["holdout_observation_ids"]),
                tuple(raw["partial_transfer_observation_ids"]),
            )
            self.record(run_id, report)
