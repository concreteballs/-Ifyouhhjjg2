# Gravitational Redshift — Mathematical Specification

## 1. Reference control

For each benchmark, x is the magnitude of the published reference-predicted fractional shift and y is the measured fractional shift:

y = F(x; θ) + error.

Candidate curves:
- Linear: F(x) = kx
- Power: F(x) = k sign(x)|x|^α
- Saturating: F(x) = sign(x)m(1 − exp(−r|x|))

The fit minimizes χ² = Σ[(F(xᵢ;θ) − yᵢ)/σᵢ]². The reported score is χ² + λK, where K is the number of fitted parameters and λ is an explicit complexity penalty.

## 2. TIK return-flow candidate

Let Πr,A and Πr,B be returned power densities at two clock locations, in W/m³. Let Π* > 0 be a declared reference power density. Define:

x_TIK = (Πr,A − Πr,B)/Π*.

A first candidate mapping is:

Δf/f = k sign(x_TIK)|x_TIK|^α.

Both k and α may be fitted. Other candidate response families can be added.

## 3. Required separation

The reference-control variable x and the TIK variable x_TIK are different inputs. They must never be silently substituted for one another. Published redshift measurements constrain the output, but do not directly measure Πr. A TIK calibration requires an independently specified way to calculate or measure Πr at each clock location.

## 4. Status

ASSUMED: candidate mapping structure.
FITTED: parameters optimized against named observations.
VALIDATED: frozen parameters tested against independent observations.
UNDERDETERMINED: too few independent observations for meaningful model-family selection.
