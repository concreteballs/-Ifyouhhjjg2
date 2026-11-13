# TIK-0: isolated research calculator

**Status:** exploratory phenomenological calculator; not a validated physical theory and not part of the Spectral Core runtime.

## Purpose

This module keeps the proposed energy of one minimum time-related event independent of rest mass. It uses an explicit finite observation volume and active-cell geometry. The provisional assumption is one candidate event per Planck volume per Planck time, multiplied by the probability that an event passes the sieve.

That Planck-scale event rate is a working hypothesis, not an established physical event rate.

## Inputs and geometry

- \`observation_volume_m3\`: finite observation volume \(V>0\);
- \`active_cell_count\`: positive integer number of active cells \(N\);
- \`cell_volume_m3\`: fixed effective volume \(v_c>0\) per cell;
- \`transmission_probability\`: event pass probability \(p\in[0,1]\);
- \`event_energy_j\`: optional energy \(\varepsilon_T\) per transmitted event;
- \`reference_power_density_w_m3\`: optional positive reference power density.

The active volume is \(V_a=Nv_c\), and it must not exceed \(V\). The active-volume fraction is \(f_V=V_a/V\).

## Equations

The provisional Planck-scale rate density is

\[
r_P=\frac{1}{l_P^3t_P}
\quad [\mathrm{events\,m^{-3}\,s^{-1}}].
\]

The total event rate and rate density are

\[
\dot N_{\mathrm{event}}=r_PpNv_c,
\qquad
r_V=\frac{\dot N_{\mathrm{event}}}{V}=r_Ppf_V.
\]

If event energy is supplied:

\[
P_T=\dot N_{\mathrm{event}}\varepsilon_T,
\qquad
\Pi_T=\frac{P_T}{V}=r_V\varepsilon_T.
\]

If a reference power density is supplied:

\[
\mathrm{TIK}_0=\frac{\Pi_T}{\Pi_{\mathrm{ref}}}.
\]

TIK-0 is a provisional dimensionless throughput ratio, not a fundamental constant and not automatically a measure of physical time dilation. J/m³ and W/m³ are not interchangeable without a declared timescale.

## Additivity and geometry

Disjoint cell volumes add. Regrouping the same cells changes nothing. Splitting a fixed active volume into more smaller cells changes nothing. At fixed cell density, scaling both active and observation volumes by the same factor scales total event rate but leaves rate density unchanged. No nonlinear grouping enhancement is included.

## Calibration

\`calibrate_event_energy()\` fits the event energy to a selected target power density. This is calibration by construction, not validation. Freeze the fitted parameter and test different independent observations. Record the target dataset and do not count it as independent confirmation.

## Minimal use

    from decimal import Decimal
    from research.tik0 import ModelInputs, calculate

    result = calculate(ModelInputs(
        observation_volume_m3=Decimal("1"),
        active_cell_count=1,
        cell_volume_m3=Decimal("0.5"),
        transmission_probability=Decimal("1"),
        event_energy_j=None,
        reference_power_density_w_m3=None,
    ))
    print(result.as_dict())

## Boundaries

- The 125 GeV resonance is not identified with the minimum event energy.
- The SI numerical value of \(c\) is not an independent calibration target.
- The architecture-level TIK for logical event compression is separate from physical TIK-0.
- Membrane breakthrough, black-hole formation, and an enlarged passage cell are outside this calculator.
- No new physical time coordinate is introduced.
- This module does not modify the Spectral Core database, routing, monitor, snapshots, or production runtime.
