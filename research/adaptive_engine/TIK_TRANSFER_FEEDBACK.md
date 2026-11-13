# TIK transfer feedback loop

## Purpose

Compare component-transfer candidates with the original TIK fit, preserve the
outcome and retain the provenance of every contributing transfer proposal.

## Evaluation rules

- Baseline and transferred candidates use the same FIT and HOLDOUT observation
  sets.
- Candidate parameters are already frozen by the transfer search before the
  HOLDOUT report is produced. Feedback performs no fitting or parameter updates.
- Positive improvement means a lower score/error than baseline.
- A candidate that fails its stability check is labelled `unstable`, even if
  its numerical HOLDOUT error is lower.
- Without an independent HOLDOUT report, the result is
  `fit_only_unverified`; FIT improvement is not treated as generalization.
- Partial-transfer observations are retained as proposal provenance only.

## Persistent history

`TransferFeedbackRegistry` stores immutable experiment reports in a versioned
JSON document. Duplicate run IDs are rejected to avoid silently overwriting
history. Component statistics count improved, regressed, unstable and
fit-only-unverified outcomes, while each candidate retains its proposal IDs,
component names and baseline comparison.

The registry is an experiment ledger, not an automatic promotion mechanism.
A future promotion policy should require repeated independent evidence and
retain rejected alternatives.
