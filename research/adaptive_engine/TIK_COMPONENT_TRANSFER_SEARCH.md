# TIK component transfer search

## Purpose

Turn partially applicable process observations into reusable, testable parameter
hints without treating those observations as ordinary training data.

## Rule contract

A `TIKTransferRule` explicitly declares:
- the shared component being transferred;
- the source raw TIK parameter and source pair side;
- the target raw TIK parameter and target pair side;
- candidate multipliers and offsets.

This allows a reusable primitive to be adapted rather than copied wholesale.
For example, a learned soft-grip response might suggest a force-sensor parameter
range for a different gripper, while a different rule maps the same primitive
to a slower response curve. Each mapping is independently testable.

## Search flow

1. The applicability pipeline classifies observations.
2. Only `PARTIAL_TRANSFER` observations can originate hints.
3. A hint is emitted only when its named component appears in that observation's
   directional transferable-component list.
4. Hints from multiple analogues are merged by target parameter and side.
5. Candidate combinations are deterministic, deduplicated and bounded.
6. Every candidate is applied to FIT observations only and passed to the raw
   TIK parameter fitter.
7. If independent HOLDOUT observations exist, the fitted candidate is frozen
   and evaluated there without refitting.

Partial observations never enter the fit call and never become direct holdout
evidence. When there is no holdout, the fit score is only an exploratory ranking.

## API

- `TIKTransferRule`: explicit component-to-parameter mapping.
- `TIKComponentHint`: source-traceable transformed values.
- `propose_tik_component_hints`: extract hints from partial observations.
- `combine_tik_transfer_hints`: bounded deterministic combinations.
- `search_tik_transfer_candidates`: fit FIT-only candidates and evaluate frozen
  candidates against HOLDOUT.

## Extension

New raw parameters and transformations can be added by extending the raw
parameter vocabulary and declaring additional rules. A rule does not assert
that a transferred parameter is correct: it creates a candidate to be tested.
Unresolved or absent components produce no hint. The component mapping is
directional; reverse transfer requires its own rule and evidence.
