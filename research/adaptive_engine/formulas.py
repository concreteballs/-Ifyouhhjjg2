"""Composable candidate response formulas."""
from __future__ import annotations
from math import exp, isfinite

FORMULAS = ("linear", "power", "saturating", "quadratic", "linear_saturating")

def predict(name: str, x: float, parameters: dict[str, float]) -> float:
    if not isfinite(x):
        raise ValueError("x must be finite")
    if name == "linear":
        y = parameters["gain"] * x + parameters.get("offset", 0.0)
    elif name == "power":
        y = parameters["gain"] * (abs(x) ** parameters["exponent"]) * (1 if x >= 0 else -1) + parameters.get("offset", 0.0)
    elif name == "saturating":
        y = parameters["cap"] * (1.0 - exp(-parameters["rate"] * abs(x))) * (1 if x >= 0 else -1) + parameters.get("offset", 0.0)
    elif name == "quadratic":
        y = parameters["linear"] * x + parameters["quadratic"] * x * x + parameters.get("offset", 0.0)
    elif name == "linear_saturating":
        z = parameters["rate"] * abs(x)
        y = parameters["gain"] * x + parameters["cap"] * (1.0 - exp(-z)) * (1 if x >= 0 else -1) + parameters.get("offset", 0.0)
    else:
        raise ValueError("unknown formula: " + name)
    if not isfinite(y):
        raise ArithmeticError("formula produced a non-finite result")
    return y
