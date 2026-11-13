# TIK-0 Mathematical Specification (research draft)

**Status:** specification draft for review; not a validated physical theory and not a production model.

**Scope:** define bookkeeping and dimensional rules for the TIK-0 phenomenological hypothesis before changing its calculator. This document does not alter the Spectral Core database, runtime, routing, monitor, or snapshots.

## 1. Model boundary

TIK-0 is a proposed phenomenological description of a hypothesized cycle:

\[
E_{\mathrm{external}} \rightarrow E_{\mathrm{time}} \rightarrow
E_{\mathrm{physical\ processes}} \rightarrow E_{\mathrm{return}}.
\]

These symbols describe the user's hypothesis, not established physical entities or mechanisms. Distinguish assumptions, derived quantities, calibrated parameters, independent tests, and unknowns. Planck length and time are scale choices derived from declared constants; their use does not establish that physical events occur once per Planck four-volume.

## 2. Geometry and event counting

Let:
- \(l_P\): Planck length, m;
- \(t_P\): Planck time, s;
- \(v_P=l_P^3\): reference Planck volume, m³;
- \(V\): finite physical observation volume, m³;
- \(N\): number of active elementary cells in that volume;
- \(v_c\): effective physical volume assigned to one active cell, m³;
- \(p\in[0,1]\): fraction/probability of candidate events transmitted through the sieve.

The active cell volume is \(V_a=Nv_c\). For a non-overlapping partition require \(0<V_a\le V\). If cells overlap, an explicit overlap/multiplicity rule is required; the same physical volume must not be silently counted twice.

The provisional Planck-scale event-rate density is

\[
r_P=\frac{1}{v_Pt_P}
\quad [\mathrm{events\,m^{-3}\,s^{-1}}].
\]

The total transmitted event rate in the observation region is

\[
\dot N_{\mathrm{event}}=r_PpV_a
=\frac{pNv_c}{l_P^3t_P}
\quad [\mathrm{events\,s^{-1}}].
\]

Normalized to the full observation volume:

\[
r_V=\frac{\dot N_{\mathrm{event}}}{V}
=r_Pp\frac{Nv_c}{V}.
\]

Define the active-volume fraction \(f_V=Nv_c/V\), so \(r_V=r_Ppf_V\).

### Additivity rule

For two disjoint groups with \(N_1\) and \(N_2\) cells of equal effective volume, total rates add: \(\dot N_{12}=\dot N_1+\dot N_2\). Grouping the same cells under one object/group identifier does not itself change the rate. Doubling the number of contributing disjoint cells doubles the total rate only when their effective volumes are also added. At fixed observation volume, subdivision or regrouping alone cannot increase normalized rate density.

This replaces the ambiguous earlier expression \(r=r_Ppn\). A bare cell count is not dimensionally sufficient without cell volume and observation volume.

## 3. Energy bookkeeping

Let \(\varepsilon_T\ge0\) be the hypothesized energy associated with one transmitted minimum event, in joules. It is an independent model parameter, not inferred from rest mass.

The incoming time-associated power in the observation region is

\[
P_T=\dot N_{\mathrm{event}}\varepsilon_T
\quad [\mathrm W].
\]

Its density over the observation volume is

\[
\Pi_T=\frac{P_T}{V}=r_V\varepsilon_T
\quad [\mathrm{W\,m^{-3}}].
\]

If fractions for physical-process and return channels are introduced later, each must have an operational definition and an explicit balance equation. They are not included in the first calculator. The calculator must not imply that the return channel has been demonstrated.

Energy density (J/m³) and power density (W/m³) are distinct. Conversion requires an explicit observation duration, e.g. \(u=\Pi_T\Delta t\) for constant power density.

## 4. Provisional physical TIK

For a reference power density \(\Pi_{\mathrm{ref}}>0\) measured or defined over the same physical region and compatible averaging convention:

\[
\mathrm{TIK}_0=\frac{\Pi_T}{\Pi_{\mathrm{ref}}}.
\]

This ratio is dimensionless. It is only a provisional normalized throughput ratio; it is not a fundamental constant and is not automatically a measure of physical time dilation.

A reference in J/m³ cannot be inserted as \(\Pi_{\mathrm{ref}}\) in W/m³ without a declared timescale and justified conversion.

The architecture-level TIK describing logical compression/density of linked historical events in Spectral Knowledge Core remains a separate data concept. No numerical identity with physical TIK is assumed.

## 5. Calibration policy

A calibration may solve for one unknown from one selected target. For example:

\[
\varepsilon_T=\frac{\Pi_{\mathrm{target}}}{r_Ppf_V}.
\]

This is a fit by construction, not independent support for the hypothesis. Mark the parameter as calibrated, record the target and dataset, and exclude that target from independent validation.

No single candidate is the universal calibration anchor:
- dark-energy density is an optional cosmological comparison, not the default target;
- the SI numerical value of \(c\) is not an independent target because it is exact by definition in SI;
- redshift is dimensionless and cannot be compared directly with power density; a derived mapping to frequency ratios is required;
- the resonance near 125 GeV is not identified with \(\varepsilon_T\) without a quantitative derivation.

## 6. Observation and test matrix

The calculator must not claim to predict an observation until a forward equation connects its variables to that observable.

| Observation | Direct measured quantity | Missing link required before prediction | Role |
|---|---|---|---|
| Laboratory gravitational redshift / optical clocks | Relative frequency ratio between clocks at different gravitational potentials | Mapping from \(\Pi_T\) or TIK to fractional frequency shift, and a predicted residual from the standard model | First controlled comparison |
| Cosmological redshift | Source and observed spectral-line frequencies | Propagation law connecting model variables to redshift vs distance/look-back time | Large-scale independent test |
| Redshift drift | Change in the same source's redshift over observer time | Time-evolution equation and sign/magnitude prediction | Long-baseline test |
| Light propagation / energy dependence | Arrival-time or phase differences between signals of different energies | Dispersion/propagation relation and conventional-medium controls | Separate test; do not redefine SI \(c\) |
| Gravitational lensing | Image positions, time delays, magnification | Metric or ray-propagation equation | Not a direct clock test |
| Dark-energy density / expansion history | Cosmological parameter estimates and expansion observables | Cosmological mapping and parameter covariance treatment | Secondary consistency check |
| Resonance near 125 GeV | Invariant-mass distributions, width, production and decay rates | Particle-level interaction/decay model | Separate microphysical test |

The first practical comparison should be laboratory clock/redshift data because the measured quantity and conditions are comparatively controlled. The standard prediction is the null baseline. TIK-0 must state a numerical residual before data are used. If no residual can be derived, the result is **not yet testable**, not a successful prediction.

## 7. Independence and anti-circularity rules

1. Use one dataset/observable for calibration at most.
2. Freeze calibrated parameters before independent tests.
3. Record shared systematics and shared source datasets; correlated measurements are not independent confirmations.
4. Compare the same observable, units, averaging window, and reference conditions.
5. Report residuals and uncertainty intervals, not only a fitted coefficient.
6. Citation count, popularity, and repeated copies of one source are not independent evidence.
7. Preserve failed predictions and parameter revisions in research history.
8. Do not add a new free parameter for each failed test without recording the loss of predictive content.

## 8. Required calculator changes (not implemented here)

Before the next code revision, replace the bare grouped-cell-count multiplier with explicit geometry inputs:
- observation_volume_m3;
- active_cell_count;
- cell_volume_m3;
- transmission_probability;
- event_energy_j;
- optional reference_power_density_w_m3.

Validation must enforce positive volumes, positive integer cell count, active volume not exceeding observation volume, valid probability, and non-negative event energy.

Outputs should include total event rate, rate density, active-volume fraction, total power, power density, and optional dimensionless TIK.

The old API must not be silently reinterpreted. A compatibility/migration decision is required. Tests must show:
- two disjoint equal-volume groups add exactly;
- regrouping the same cells changes nothing;
- splitting fixed active volume into more smaller cells changes nothing;
- increasing active volume at fixed cell density increases total rate, while rate density stays unchanged if observation volume scales with it;
- increasing active-volume fraction at fixed observation volume increases rate density linearly;
- invalid geometry is rejected;
- calibration reproduces its target but is labelled calibration, not validation.

## 9. Explicit exclusions

This specification does not model membrane rupture, black-hole formation, a single enlarged passage cell, the interior state of a black hole, or a collective interpretation of the 125 GeV resonance. These remain separate hypotheses until their variables and testable consequences are specified.

It introduces no new physical time coordinate. Calendar time remains the ordinary time coordinate in the knowledge architecture. Any relationship between event density and physical clock rates requires a separate forward model.

## 10. Decision gate before implementation

The following choices must be confirmed before changing calculator code:

1. Does one active cell represent a fixed effective physical volume \(v_c\), or is cell volume itself variable?
2. Is observation volume \(V\) a laboratory region, cosmological region, or abstract normalization volume? First implementation should use a declared finite region.
3. Does \(p\) mean probability that a candidate event passes the membrane, or average fraction of active cells? These interpretations must not be mixed.
4. Is \(\varepsilon_T\) energy per transmitted event, before or after any later partition into process/return channels?

Until these choices are fixed, this is a review artifact and the calculator remains unchanged.
