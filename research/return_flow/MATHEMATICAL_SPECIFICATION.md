# Return Flow Model — Mathematical Specification

## 1. Normalized load

Let incoming power density be Πin [W/m³] and a declared reference power density be Π* > 0 [W/m³]. Define x = Πin / Π*.

Let active volume fraction, return probability and return efficiency be fV, pr, ηr ∈ [0, 1]. Their explicit channel multiplier is q = fV pr ηr.

## 2. Candidate response curves

With coefficient k > 0 and cap 0 < m ≤ 1:

- Linear: gL(x) = min(m, kx)
- Power: gP(x) = min(m, kx^α), α > 0
- Saturating: gS(x) = m(1 − exp(−kx))

Returned fraction and power density:

fr = min(1, q g(x))
Πr = Πin fr
Πretained = Πin − Πr

## 3. Dynamic candidate

A delayed response relaxes toward the saturating target gS(xt):

ft = gS(xt) + (ft−1 − gS(xt)) exp(−Δt/τ), τ > 0.

The first sample starts from zero return state. The implementation fits this state curve against time-ordered observations.

## 4. Parameter fitting

For observations (xi, yi), candidate parameters minimize RMSE = sqrt(sum((ŷi − yi)^2) / n).

Optional score = RMSE + λK/n, where K is the number of fitted parameters and λ ≥ 0. The default λ = 0 ranks by fit error only. Grid search is deterministic and its candidate grid is explicit input.

## 5. Status

ASSUMED = working structural choice; FITTED = parameter selected against a named dataset; VALIDATED = frozen model tested successfully on independent data. A low training RMSE alone never changes FITTED into VALIDATED.
