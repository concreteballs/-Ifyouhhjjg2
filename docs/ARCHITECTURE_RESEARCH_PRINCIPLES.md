# Architecture research principles

Status: owner-approved architectural direction, 2026-11-12.
This document records design principles. It does not assert that speculative
physical hypotheses are established facts or authorize implementation before
the relevant package is designed and approved.

## 1. Knowledge is not a binary true/false ledger

An assertion, its evidence, its applicability conditions, and its revision
history are separate records. New evidence may narrow or replace an assertion's
scope without deleting historically valid observations or independent
conclusions derived from the same research.

Examples to preserve in tests and model design:
- Historical comparisons of Damascus/Bulat steel must name the comparator set,
  test method, specimen preparation, and period.
- Newtonian mechanics remains useful within a defined accuracy and parameter
  range; a broader theory does not erase its valid domain.
- A claim about a material's property must not be conflated with the evidence
  supporting a separate claim about composition or processing.

## 2. Time is a first-class research dimension

Keep a common chronology, but do not assume that all regions of knowledge
change at the same rate. The model must be able to represent:
- when an event or phenomenon was valid in the world;
- when the system learned or recorded it;
- when it was tested or reassessed;
- the conditions and interval over which a claim applies;
- local density of knowledge-changing events and local fluctuations in
  research activity.

A useful initial measurable quantity is local event density:

    rho(x,t) = Delta N(x,t) / Delta t

Here x identifies a knowledge region, t is common chronology, and Delta N
counts qualifying changes in that region. This is initially a measure of
knowledge activity, not a claim that physical time itself has been measured
to flow faster there.

The architecture must leave room to compare this operational measure with
stronger hypotheses about local temporal structure. Do not hard-code either
homogeneous or fluctuating physical time as an established truth.

## 3. Local regions, gradients, and transitions

Knowledge regions may develop as partially independent islands. A region may
accumulate dense local relations while their relevance decreases outside it.
Cross-region transitions should preserve the chain of intermediate concepts,
the type of each relation, the abstraction distance, and the evidence for each
step.

The gradient coefficient must be calibrated against known cases and tested on
held-out cases. It must not be selected only because it makes a desired
connection appear strong. Reserved transition regions and their protected
coordinates remain outside the current database package scope.

## 4. Discovery must lead to testable hypotheses

The system should search for structural and functional patterns across
distant domains, then propose new combinations that can be tested. It must
distinguish:
- established facts and their evidence;
- plausible extrapolations;
- novel hypotheses;
- experimental predictions;
- observations that confirm, constrain, or refute those predictions.

Example research path: infer a possible relationship between controlled
microstructure and material properties from historical patterned steels,
powder metallurgy, alloy design, and additive manufacturing. This is a
research lead, not a claim that reproducing a dendritic pattern will
automatically improve a steel. Phase stability, carbide distribution, grain
boundaries, defects, residual stress, and heat treatment all require testing.

## 5. Uncertainty and hidden state are research topics, not presets

Keep distinct:
- uncertainty due to incomplete knowledge of a system's state;
- statistical variability under a specified model;
- deterministic unpredictability caused by sensitivity to initial conditions;
- quantum probabilities and their interpretation;
- any proposed irreducible or ontic uncertainty.

The owner's working hypothesis explores whether apparent uncertainty may be
relative to an observer and to the accessible state description, and whether
a deeper undetermined initial condition could underlie the emergence of a
universe. This remains a hypothesis, not a database truth value.

The proposed coupled-metronome experiment is a possible test of residual
memory after an operational reset. A statistically detectable dependence on
the prior partition would support the presence of hidden memory in the
apparatus or environment; by itself it would not prove absolute randomness or
a cosmological origin. A null result would set a sensitivity-dependent bound,
not prove the absence of all hidden state.

## 6. Snapshots and history

A full database copy after every change is not required. Use a separate
append-only change history together with periodic full or scoped checkpoints.
Restore a state by loading the nearest earlier checkpoint and replaying
subsequent changes. Unchanged blocks may be content-addressed and reused.

The history must distinguish an event's world-valid time from the time the
system recorded or revised it. Hierarchy snapshots in extensions.py remain
structural checkpoints of object hierarchy; they are not whole-system history.

## 7. Research hypotheses must remain revisable

The project must not force all future discoveries into today's assumptions
about time, causality, geometry, probability, or physical ontology. New models
must be compared with observations and competing explanations. A speculative
model may be stored and explored without being silently promoted to established
knowledge.

## 8. Implementation boundary

These principles guide future packages. They do not authorize changes to
routing, the meta-router, the guard network, or the spectral adder during the
current database/epistemic-design phase. Packages 1–3 remain the completed
baseline; Package 4 must be specified before its schema migration is written.
