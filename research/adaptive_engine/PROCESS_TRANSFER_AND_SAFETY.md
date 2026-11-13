# Process analogy, skill transfer and execution safety

This layer extends the Adaptive Engine from model fitting to reusable process knowledge.

## Process analogy

A `ProcessProfile` records process family, structure, function, conditions, regimes, input/output schemas with units, operating ranges, capabilities and provenance. `assess_process_transfer(source, target)` is directional: assess the reverse direction separately. It reports each comparison axis and the exact transferable components; it does not collapse everything into one similarity score.

Different process families can still share components. A glider and a powered aircraft may share energy management or trajectory-control primitives while differing in engine-specific operations. Partial analogues are useful for component transfer, but are not direct validation observations.

## Dataset roles and holdout

`build_applicability_split` assigns `FIT`, `HOLDOUT`, `PARTIAL_TRANSFER`, `ADAPTATION_REQUIRED`, `EXCLUDED` or `UNRESOLVED`. Fit and holdout groups are supplied explicitly, not randomized at point level. A holdout additionally needs independent provenance/lineage. Unknown provenance never silently becomes a holdout. Partial analogues can transfer listed components but cannot be counted as direct holdout evidence.

## Task composition

Tasks are decomposed into named operations with prerequisites. `cluster_tasks` groups tasks sharing operations. `plan_skill_transfer(source, target)` identifies reusable operations, missing operations, context/tag adaptations and calibration requirements. Direction is explicit; reversing the arguments produces a separate plan.

Example: a grasp skill learned on a soft overripe peach can contribute the grip primitive to a glass-handling task, but the target requires a different force regime and calibration. A milk-carton compression task can reuse the same hand-closing primitive with a different target policy.

## Calibration

`fit_calibration` fits a linear correction from known reference measurements. The profile reports residual error and a validated range. A calibration is not considered valid outside its observed reference range or when its residual exceeds the configured tolerance. A compliant physical controller must fail closed when calibration is absent, stale or out of range.

## Knowledge versus execution

`CapabilityKnowledge` represents what a model has learned; it does not grant permission to execute. `authorize_execution` is a fail-closed policy decision requiring authenticated identity, explicitly authorized environment and scope, human/dual approval by risk tier, sandboxing for high-risk operations, and calibration plus emergency-stop interlocks for physical actuation. Certain harmful domains are categorically denied.

This is a policy layer, not a security boundary by itself. Production use still requires an independently enforced authorization service, signed approvals, least-privilege actuator interfaces, immutable audit logs and hardware/software interlocks. A model must never be able to grant itself permissions or bypass the external controller.

## Integrated TIK research loop

`fit_tik_research_dataset` connects process applicability to the existing paired TIK adapter. Every record carries a TIK pair, a process profile and a provenance group. Classification happens first; only `FIT` observations are used to optimize. Partial analogues remain visible as component-transfer material. Independent `HOLDOUT` observations are evaluated afterward using the frozen selected configuration, with predictions and error metrics returned separately. Holdout data are never used to refit the selected parameters.

Example: a paired TIK observation from a process that shares only a return-response component can be retained as `PARTIAL_TRANSFER`; it does not become a training sample or a direct holdout score merely because one feature overlaps.
