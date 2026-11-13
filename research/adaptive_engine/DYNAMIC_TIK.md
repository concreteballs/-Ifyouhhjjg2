# Dynamic TIK fitting

The temporal adapter evaluates each observation through the existing TIK-0 and return-flow calculations, then applies the existing first-order relaxation function to the steady-state return fraction.

The fitter searches jointly over:
- return model family;
- return coefficient and power exponent;
- relaxation time constant;
- initial return fraction.

It ranks complete time-series configurations by weighted RMSE and retains all alternatives. Input timestamps must be strictly increasing. The model uses the first timestamp as the time origin and the configured initial fraction as the initial state.

This is a first temporal state model. It currently uses one relaxation state and a first-order response; multi-state memory, hysteresis and automatic discovery of additional state variables remain future extensions.
