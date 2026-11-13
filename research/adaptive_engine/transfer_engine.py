"""Process analogy, task composition, directed transfer and sensor calibration."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from math import isfinite, sqrt
from typing import Iterable


class Applicability(str, Enum):
    DIRECT = "DIRECT"
    PARTIAL = "PARTIAL"
    CONDITIONAL = "CONDITIONAL"
    INCOMPATIBLE = "INCOMPATIBLE"
    UNKNOWN = "UNKNOWN"


class AxisStatus(str, Enum):
    MATCH = "MATCH"
    PARTIAL = "PARTIAL"
    MISMATCH = "MISMATCH"
    UNKNOWN = "UNKNOWN"


class DatasetRole(str, Enum):
    FIT = "FIT"
    HOLDOUT = "HOLDOUT"
    PARTIAL_TRANSFER = "PARTIAL_TRANSFER"
    ADAPTATION_REQUIRED = "ADAPTATION_REQUIRED"
    EXCLUDED = "EXCLUDED"
    UNRESOLVED = "UNRESOLVED"


@dataclass(frozen=True)
class ProcessProfile:
    profile_id: str
    process_family: str
    structural: tuple[str, ...] = ()
    functional: tuple[str, ...] = ()
    conditions: tuple[str, ...] = ()
    regimes: tuple[str, ...] = ()
    inputs: tuple[tuple[str, str], ...] = ()
    outputs: tuple[tuple[str, str], ...] = ()
    ranges: tuple[tuple[str, float, float], ...] = ()
    capabilities: tuple[str, ...] = ()
    source_id: str = ""
    experiment_id: str = ""
    lineage_ids: tuple[str, ...] = ()
    required_components: tuple[str, ...] = ()

    def __post_init__(self):
        if not self.profile_id.strip() or not self.process_family.strip():
            raise ValueError("profile_id and process_family are required")
        for name in ("structural", "functional", "conditions", "regimes",
                     "capabilities", "lineage_ids", "required_components"):
            values = getattr(self, name)
            if len(values) != len(set(values)):
                raise ValueError(name + " must not contain duplicates")
        for name in ("inputs", "outputs"):
            values = getattr(self, name)
            if len({key for key, _ in values}) != len(values):
                raise ValueError(name + " variable names must be unique")
        for _, low, high in self.ranges:
            if not isfinite(low) or not isfinite(high) or low > high:
                raise ValueError("ranges must be finite and ordered")


@dataclass(frozen=True)
class AxisAssessment:
    axis: str
    status: AxisStatus
    shared: tuple[str, ...] = ()
    source_only: tuple[str, ...] = ()
    target_only: tuple[str, ...] = ()


@dataclass(frozen=True)
class ProcessAssessment:
    source_id: str
    target_id: str
    model_family: str
    applicability: Applicability
    axes: tuple[AxisAssessment, ...]
    transferable_components: tuple[str, ...]
    independent: bool | None
    rationale: tuple[str, ...]


def _compare(name, left, right):
    a, b = set(left), set(right)
    if not a or not b:
        return AxisAssessment(name, AxisStatus.UNKNOWN)
    shared, only_a, only_b = tuple(sorted(a & b)), tuple(sorted(a - b)), tuple(sorted(b - a))
    status = AxisStatus.MATCH if not only_a and not only_b else AxisStatus.PARTIAL if shared else AxisStatus.MISMATCH
    return AxisAssessment(name, status, shared, only_a, only_b)


def _compare_schema(name, left, right):
    a, b = dict(left), dict(right)
    if not a or not b:
        return AxisAssessment(name, AxisStatus.UNKNOWN)
    shared = tuple(sorted(k for k in a.keys() & b.keys() if a[k] == b[k]))
    mismatch = tuple(sorted(k + " (unit mismatch)" for k in a.keys() & b.keys() if a[k] != b[k]))
    only_a = tuple(sorted(set(a) - set(b))) + mismatch
    only_b = tuple(sorted(set(b) - set(a))) + mismatch
    status = AxisStatus.MATCH if not only_a and not only_b else AxisStatus.PARTIAL if shared else AxisStatus.MISMATCH
    return AxisAssessment(name, status, shared, only_a, only_b)


def _compare_ranges(left, right):
    a, b = {k: (lo, hi) for k, lo, hi in left}, {k: (lo, hi) for k, lo, hi in right}
    if not a or not b:
        return AxisAssessment("ranges", AxisStatus.UNKNOWN)
    shared, only_a, only_b = [], [], []
    for key in sorted(a.keys() & b.keys()):
        lo, hi = a[key]
        other_lo, other_hi = b[key]
        if max(lo, other_lo) <= min(hi, other_hi):
            shared.append(key)
        else:
            only_a.append(key + " (disjoint)")
            only_b.append(key + " (disjoint)")
    only_a.extend(sorted(set(a) - set(b)))
    only_b.extend(sorted(set(b) - set(a)))
    status = AxisStatus.MATCH if not only_a and not only_b else AxisStatus.PARTIAL if shared else AxisStatus.MISMATCH
    return AxisAssessment("ranges", status, tuple(shared), tuple(only_a), tuple(only_b))


def assess_process_transfer(source: ProcessProfile, target: ProcessProfile,
                            *, model_family="general") -> ProcessAssessment:
    """Assess source -> target. Reverse direction must be assessed independently."""
    if not model_family.strip():
        raise ValueError("model_family is required")
    axes = (
        _compare("family", (source.process_family,), (target.process_family,)),
        _compare("structure", source.structural, target.structural),
        _compare("function", source.functional, target.functional),
        _compare("conditions", source.conditions, target.conditions),
        _compare("regimes", source.regimes, target.regimes),
        _compare_schema("inputs", source.inputs, target.inputs),
        _compare_schema("outputs", source.outputs, target.outputs),
        _compare_ranges(source.ranges, target.ranges),
        _compare("capabilities", source.capabilities, target.capabilities),
    )
    left = set(source.lineage_ids) | {v for v in (source.source_id, source.experiment_id) if v}
    right = set(target.lineage_ids) | {v for v in (target.source_id, target.experiment_id) if v}
    independent = (not bool(left & right)) if left and right else None
    # Both named capabilities and functional primitives can transfer independently.
    target_needs = set(target.required_components or target.capabilities)
    transferable = tuple(sorted((set(source.capabilities) & target_needs)
                                | (set(source.functional) & set(target.functional))))
    mismatch = any(a.status == AxisStatus.MISMATCH for a in axes)
    unknown = any(a.status == AxisStatus.UNKNOWN for a in axes)
    reasons = []
    if unknown and not transferable:
        result = Applicability.UNKNOWN
        reasons.append("Missing profile data prevents a reliable classification.")
    elif mismatch:
        result = Applicability.PARTIAL if transferable else Applicability.INCOMPATIBLE
        reasons.append("At least one axis differs; only explicitly shared components are transferable.")
    elif unknown:
        result = Applicability.UNKNOWN
        reasons.append("Missing profile data prevents a reliable classification.")
    elif all(a.status == AxisStatus.MATCH for a in axes):
        result = Applicability.DIRECT
        reasons.append("All declared process dimensions match.")
    else:
        result = Applicability.PARTIAL
        reasons.append("Some dimensions overlap while others differ.")
    if independent is False:
        reasons.append("Shared provenance/lineage prevents independent holdout use.")
        if result == Applicability.DIRECT:
            result = Applicability.CONDITIONAL
    elif independent is None:
        reasons.append("Provenance is insufficient to establish independence.")
    return ProcessAssessment(source.profile_id, target.profile_id, model_family,
        result, axes, transferable, independent, tuple(reasons))


@dataclass(frozen=True)
class DatasetObservation:
    observation_id: str
    group_id: str
    profile: ProcessProfile


@dataclass(frozen=True)
class ObservationRole:
    observation_id: str
    group_id: str
    role: DatasetRole
    assessment: ProcessAssessment


def build_applicability_split(reference: ProcessProfile, observations: Iterable[DatasetObservation],
                              *, fit_group_ids: Iterable[str], holdout_group_ids: Iterable[str],
                              model_family: str):
    """Group-aware split: partial analogues transfer components, never masquerade as holdouts."""
    data = tuple(observations)
    fit, holdout = set(fit_group_ids), set(holdout_group_ids)
    if fit & holdout:
        raise ValueError("fit and holdout groups must be disjoint")
    if len({x.observation_id for x in data}) != len(data):
        raise ValueError("observation IDs must be unique")
    result = []
    for item in data:
        assessment = assess_process_transfer(reference, item.profile, model_family=model_family)
        if assessment.applicability == Applicability.INCOMPATIBLE:
            role = DatasetRole.EXCLUDED
        elif assessment.applicability == Applicability.UNKNOWN:
            role = DatasetRole.UNRESOLVED
        elif assessment.applicability == Applicability.PARTIAL:
            role = DatasetRole.PARTIAL_TRANSFER
        elif assessment.applicability == Applicability.CONDITIONAL:
            role = DatasetRole.ADAPTATION_REQUIRED
        elif item.group_id in fit:
            role = DatasetRole.FIT
        elif item.group_id in holdout and assessment.independent is True:
            role = DatasetRole.HOLDOUT
        elif assessment.applicability == Applicability.CONDITIONAL:
            role = DatasetRole.ADAPTATION_REQUIRED
        else:
            role = DatasetRole.UNRESOLVED
        result.append(ObservationRole(item.observation_id, item.group_id, role, assessment))
    return tuple(result)


@dataclass(frozen=True)
class TaskOperation:
    operation_id: str
    prerequisites: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
    requires_calibration: bool = False


@dataclass(frozen=True)
class TaskDefinition:
    task_id: str
    operations: tuple[TaskOperation, ...]
    context_tags: tuple[str, ...] = ()

    def __post_init__(self):
        if not self.task_id.strip() or not self.operations:
            raise ValueError("task_id and operations are required")
        ids = {op.operation_id for op in self.operations}
        if len(ids) != len(self.operations):
            raise ValueError("operation IDs must be unique")
        if any(set(op.prerequisites) - ids for op in self.operations):
            raise ValueError("every prerequisite must be defined in the task")
        graph = {op.operation_id: set(op.prerequisites) for op in self.operations}
        visiting, visited = set(), set()
        def visit(node):
            if node in visiting:
                raise ValueError("operation dependency cycle")
            if node in visited:
                return
            visiting.add(node)
            for parent in graph[node]:
                visit(parent)
            visiting.remove(node)
            visited.add(node)
        for node in graph:
            visit(node)


@dataclass(frozen=True)
class TaskCluster:
    cluster_id: str
    task_ids: tuple[str, ...]
    reusable_operations: tuple[str, ...]


@dataclass(frozen=True)
class TransferPlan:
    source_task_id: str
    target_task_id: str
    transferable_operations: tuple[str, ...]
    missing_operations: tuple[str, ...]
    adaptation_operations: tuple[str, ...]
    requires_calibration: tuple[str, ...]


def cluster_tasks(tasks: Iterable[TaskDefinition]):
    """Connected components of tasks sharing one or more named operations."""
    data = tuple(tasks)
    if len({t.task_id for t in data}) != len(data):
        raise ValueError("task IDs must be unique")
    parent = list(range(len(data)))
    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    op_sets = [{op.operation_id for op in t.operations} for t in data]
    for i in range(len(data)):
        for j in range(i + 1, len(data)):
            if op_sets[i] & op_sets[j]:
                parent[root(j)] = root(i)
    groups = {}
    for i, task in enumerate(data):
        groups.setdefault(root(i), []).append((task, op_sets[i]))
    result = []
    for members in groups.values():
        counts = {}
        for _, ops in members:
            for op in ops:
                counts[op] = counts.get(op, 0) + 1
        ids = tuple(sorted(task.task_id for task, _ in members))
        shared = tuple(sorted(op for op, count in counts.items() if count > 1))
        result.append(TaskCluster("cluster:" + "+".join(ids), ids, shared))
    return tuple(sorted(result, key=lambda x: x.cluster_id))


def plan_skill_transfer(source: TaskDefinition, target: TaskDefinition):
    """Directed source -> target transfer. Call again in reverse for reciprocal transfer."""
    src = {op.operation_id: op for op in source.operations}
    dst = {op.operation_id: op for op in target.operations}
    shared = set(src) & set(dst)
    reusable = set(shared)
    changed = True
    while changed:
        changed = False
        for key in tuple(reusable):
            if not set(dst[key].prerequisites).issubset(reusable):
                reusable.remove(key)
                changed = True
    adaptation = {key for key in shared if src[key].tags != dst[key].tags
                  or source.context_tags != target.context_tags}
    calibration = {key for key in shared if dst[key].requires_calibration}
    return TransferPlan(source.task_id, target.task_id, tuple(sorted(reusable)),
        tuple(sorted(set(dst) - reusable)), tuple(sorted(adaptation)),
        tuple(sorted(calibration)))


@dataclass(frozen=True)
class CalibrationPoint:
    reference_value: float
    sensor_reading: float


@dataclass(frozen=True)
class CalibrationProfile:
    slope: float
    intercept: float
    reference_min: float
    reference_max: float
    max_residual: float
    rmse: float
    sample_count: int
    accepted: bool

    def correct(self, reading: float):
        if not isfinite(reading):
            raise ValueError("sensor reading must be finite")
        return self.slope * reading + self.intercept

    def valid_for(self, low: float, high: float, *, maximum_residual: float):
        return (self.accepted and self.max_residual <= maximum_residual
                and low >= self.reference_min and high <= self.reference_max and low <= high)


def fit_calibration(points: Iterable[CalibrationPoint], *, maximum_residual: float):
    """Fit a linear sensor correction against known reference measurements."""
    data = tuple(points)
    if len(data) < 2 or not isfinite(maximum_residual) or maximum_residual < 0:
        raise ValueError("at least two points and a non-negative residual limit are required")
    if any(not isfinite(p.reference_value) or not isfinite(p.sensor_reading) for p in data):
        raise ValueError("calibration values must be finite")
    x, y = [p.sensor_reading for p in data], [p.reference_value for p in data]
    mx, my = sum(x) / len(x), sum(y) / len(y)
    variance = sum((v - mx) ** 2 for v in x)
    if variance <= 0:
        raise ValueError("sensor readings must span at least two distinct values")
    slope = sum((a - mx) * (b - my) for a, b in zip(x, y)) / variance
    if abs(slope) < 1e-15:
        raise ValueError("calibration slope is effectively zero")
    intercept = my - slope * mx
    residuals = [abs(slope * a + intercept - b) for a, b in zip(x, y)]
    maximum = max(residuals)
    rmse = sqrt(sum(v * v for v in residuals) / len(residuals))
    return CalibrationProfile(slope, intercept, min(y), max(y), maximum, rmse,
                              len(data), maximum <= maximum_residual)
