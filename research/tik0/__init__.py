"""Isolated research prototype for the initial temporal-information coefficient."""
from .model import ModelInputs, ModelResult, calibrate_event_energy, calculate, planck_scales\nfrom .local_state import TIKLocalStateInputs, TIKLocalStateResult, calculate_local_state

__all__ = ["ModelInputs", "ModelResult", "calibrate_event_energy", "calculate", "planck_scales", "TIKLocalStateInputs", "TIKLocalStateResult", "calculate_local_state"]
