# Redshift Benchmark Fit — Initial Calibration

**Branch:** research/tik0-prototype  
**Dataset:** two published aggregate experiments  
**Status:** FITTED / UNDERDETERMINED

## Input observations

| Experiment | Reference shift | Measured shift | 1σ uncertainty |
|---|---:|---:|---:|
| Pound–Rebka, two-way 22.5 m comparison | 4.885 × 10⁻¹⁵ | 5.13 × 10⁻¹⁵ | 0.51 × 10⁻¹⁵ |
| Zheng et al. 2023, 1 cm optical-clock gradient | 10.9 × 10⁻¹⁹ | 12.4 × 10⁻¹⁹ | 2.6 × 10⁻¹⁹ |

## First fitted relationship

The reference-control model is:

y = kx

A weighted least-squares calculation over the two aggregate observations gives approximately:

- k = 1.064
- 1σ parameter uncertainty ≈ 0.096
- χ² at k = 1.064 ≈ 0.113
- reduced χ² is not interpreted because there are only two aggregate observations and one fitted parameter.

The repository grid fitter selects the linear candidate with k = 1.064. The next simplest candidates are penalized for an additional free parameter. This is a calibration of the published reference-potential input, not a TIK return-flow result.

The fitted coefficient is statistically compatible with k = 1. The current data therefore do not indicate a meaningful departure from the reference redshift relation.

## What this establishes

- The benchmark data and uncertainties can be loaded into a reproducible fitter.
- A simple linear mapping describes these two aggregate results within their stated uncertainties.
- More flexible curves cannot be meaningfully distinguished with only two aggregate observations.
- Both records are aggregate results, not the underlying raw pairwise measurements.

## What remains unavailable

Neither experiment measures the TIK return-flow contrast ΔΠ_return. Therefore no coefficient connecting TIK-0 to gravitational redshift has yet been fitted. That requires a defined calculation of return-flow density at both clock locations, followed by independent observations or a justified mapping from measured geometry to the TIK inputs.

## Sources

- Pound–Rebka measurement and quoted prediction: https://paulba.no/pdf/PoundRebka.pdf ; original paper DOI: https://doi.org/10.1103/PhysRevLett.4.337
- Zheng et al. (2023), Nature Communications 14, 4886: https://pmc.ncbi.nlm.nih.gov/articles/PMC10423269/ ; DOI: https://doi.org/10.1038/s41467-023-40629-8
