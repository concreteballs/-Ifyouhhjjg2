"""Knowledge retention and fail-closed authorization for execution."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum


class AuthorizationStatus(str, Enum):
    KNOWLEDGE_ONLY = "KNOWLEDGE_ONLY"
    ALLOWED = "ALLOWED"
    DENIED = "DENIED"


@dataclass(frozen=True)
class CapabilityKnowledge:
    capability_id: str
    components: tuple[str, ...]
    description: str = ""

    def __post_init__(self):
        if not self.capability_id.strip() or not self.components:
            raise ValueError("capability ID and components are required")


@dataclass(frozen=True)
class ExecutionRequest:
    capability_id: str
    domain: str
    risk_tier: int
    authenticated: bool = False
    environment_authorized: bool = False
    explicit_scope_match: bool = False
    human_approval: bool = False
    second_approver: bool = False
    sandboxed: bool = False
    physical_actuation: bool = False
    calibration_valid: bool = False
    emergency_stop_available: bool = False


@dataclass(frozen=True)
class SafetyPolicy:
    autonomous_risk_ceiling: int = 1
    human_approval_from: int = 2
    dual_approval_from: int = 4
    absolute_deny_domains: tuple[str, ...] = (
        "weapon_use", "deliberate_harm", "unauthorized_access",
        "critical_infrastructure_sabotage", "destructive_interference",
    )


@dataclass(frozen=True)
class AuthorizationDecision:
    status: AuthorizationStatus
    reasons: tuple[str, ...]
    knowledge_retained: bool = True


def authorize_execution(request: ExecutionRequest, policy: SafetyPolicy = SafetyPolicy(),
                        *, execution_requested=True):
    """Policy decision only; it does not itself grant actuator or system permissions."""
    if not execution_requested:
        return AuthorizationDecision(AuthorizationStatus.KNOWLEDGE_ONLY,
            ("Knowledge is retained; no execution was requested.",))
    if not request.capability_id.strip() or not request.domain.strip() or not 0 <= request.risk_tier <= 5:
        return AuthorizationDecision(AuthorizationStatus.DENIED, ("Invalid capability, domain or risk tier.",))
    if request.domain in policy.absolute_deny_domains:
        return AuthorizationDecision(AuthorizationStatus.DENIED,
            ("This action domain is categorically outside the execution policy.",))
    reasons = []
    if not request.authenticated:
        reasons.append("Authenticated execution identity is required.")
    if not request.environment_authorized:
        reasons.append("Target environment is not explicitly authorized.")
    if not request.explicit_scope_match:
        reasons.append("Requested action is outside the approved scope.")
    if request.risk_tier > policy.autonomous_risk_ceiling and not request.human_approval:
        reasons.append("Human approval is required for this risk tier.")
    if request.risk_tier >= policy.dual_approval_from and not request.second_approver:
        reasons.append("Independent second approval is required.")
    if request.risk_tier >= policy.human_approval_from and not request.sandboxed:
        reasons.append("High-risk operations must first be confined to a sandbox.")
    if request.physical_actuation and not request.calibration_valid:
        reasons.append("Valid in-range calibration is required before physical actuation.")
    if request.physical_actuation and not request.emergency_stop_available:
        reasons.append("Verified emergency stop/interlock is required.")
    if reasons:
        return AuthorizationDecision(AuthorizationStatus.DENIED, tuple(reasons))
    return AuthorizationDecision(AuthorizationStatus.ALLOWED,
        ("Configured authorization gates passed; downstream actuator controls still apply.",))
