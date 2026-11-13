# TIK-0: isolated research calculator

**Status:** exploratory prototype; not part of the Spectral Core runtime.

## Purpose

This module turns the initial hypothesis into a dimensionally explicit calculation.
It keeps the energy of a minimum time-related event independent from rest mass.
The provisional assumptions are one candidate event per Planck time and Planck
volume, with an explicit transmission probability and count of grouped cells.

## Equations

Planck scales are derived from the declared constants:

- l_P = sqrt(hbar G / c^3)
- t_P = sqrt(hbar G / c^5)
- V_P = l_P^3
- R_P = 1 / (V_P t_P)

For transmission probability p, grouped cell count n, and event energy epsilon_T:

- event throughput: R = R_P p n, in events/(m3 s);
- energy-flow density: Pi_T = R epsilon_T, in W/m3;
- optional dimensionless coefficient: TIK_0 = Pi_T / Pi_ref.

Ordinary grouping is additive: two equal contributing cells produce twice the
throughput of one. This version does not add a nonlinear enhancement term.
The black-hole/membrane-breakthrough transition is a separate regime and is
intentionally outside this first calculator.

## Unknowns and calibration

event_energy_j is deliberately not inferred from particle rest mass. It may
represent the model's proposed energy of a minimum time-related event.

reference_power_density_w_m3 must be explicitly supplied before TIK-0 can be
computed. An energy density in J/m3 is not interchangeable with a power density
in W/m3. If an energy-density observation is used, an explicit observation
timescale is needed to convert it into a power density.

calibrate_event_energy() can solve for the event energy that reproduces a
chosen target. This is calibration, not validation. After calibration, freeze
the parameter and test a different, independent observation.

No default event energy or reference value is invented. With unknown values,
the calculator reports event throughput and leaves power density and TIK-0 unset.

## Minimal use

    from decimal import Decimal
    from research.tik0 import ModelInputs, calculate

    result = calculate(ModelInputs(
        event_energy_j=None,
        transmission_probability=Decimal("1"),
        grouped_cell_count=1,
        reference_power_density_w_m3=None,
    ))
    print(result.as_dict())

## Boundaries

- The 125 GeV collider resonance is not assumed to be the minimum event energy.
  A collective-state interpretation remains a separate hypothesis.
- Massless particles are not included in this first pass.
- Planck length/time are provisional scale choices, not proof that the proposed
  physical events exist at those scales.
- The module does not modify the Spectral Core database, routing, monitor,
  snapshots, or production runtime.
