"""Independent clock/redshift measurements used by the TIK profile study.

The records preserve the distinction between training, external calibration,
and held-out validation. They are not TIK-specific measurements.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import sqrt

C_M_S = 299_792_458.0
G_LOCAL_M_S2 = 9.81


@dataclass(frozen=True)
class ClockBenchmark:
    name: str
    height_equivalent_m: float
    observed_fractional_shift: float
    observed_sigma: float
    reference_fractional_shift: float
    role: str
    source_url: str
    source_doi: str
    notes: str


# 14 blinded measurement-run gradients from Zheng et al. Fig. 3a.
# Units: 1e-19 per cm; sign is converted to magnitude for this comparison.
ZHENG_2023_RUNS = (
    (15.721620183759372, 2.713345735661244),
    (10.736818123880271, 2.8036991409782464),
    (15.548702170621842, 2.4202905635924647),
    (9.225705555466803, 2.706147515263497),
    (13.988537727206191, 2.3371621136681178),
    (15.370872509007581, 2.3325484490876427),
    (13.118142217697956, 2.5340433927948562),
    (9.09822510370597, 3.1695239616389554),
    (7.655670267514898, 2.7899304948897017),
    (12.121450818277694, 2.3668142264087844),
    (14.637711618202216, 2.558214957984931),
    (9.53618024534607, 2.2823978838850656),
    (8.67545063419641, 3.0773636397390804),
    (13.442899820387119, 2.1992767058597873),
)

ZHENG_SYSTEMATIC_GRADIENT_SIGMA_1E19_PER_CM = 2.5


def zheng_training_summary() -> dict[str, float | int]:
    weights = [1.0 / (sigma * sigma) for _, sigma in ZHENG_2023_RUNS]
    mean = sum(w * value for w, (value, _) in zip(weights, ZHENG_2023_RUNS)) / sum(weights)
    statistical_sigma = sqrt(1.0 / sum(weights))
    total_sigma = sqrt(
        statistical_sigma**2 + ZHENG_SYSTEMATIC_GRADIENT_SIGMA_1E19_PER_CM**2
    )
    # A one-centimetre separation converts the gradient per cm to a fractional shift.
    return {
        "run_count": len(ZHENG_2023_RUNS),
        "weighted_gradient_1e19_per_cm": mean,
        "statistical_sigma_1e19_per_cm": statistical_sigma,
        "systematic_sigma_1e19_per_cm": ZHENG_SYSTEMATIC_GRADIENT_SIGMA_1E19_PER_CM,
        "total_sigma_1e19_per_cm": total_sigma,
        "training_shift_1cm": mean * 1e-19,
        "training_sigma_1cm": total_sigma * 1e-19,
    }


_ZHENG = zheng_training_summary()
ZHENG_2023_TRAINING = ClockBenchmark(
    name="Zheng et al. 2023, five-ensemble optical-clock array",
    height_equivalent_m=0.01,
    observed_fractional_shift=float(_ZHENG["training_shift_1cm"]),
    observed_sigma=float(_ZHENG["training_sigma_1cm"]),
    reference_fractional_shift=10.9e-19,
    role="TRAINING",
    source_url="https://zenodo.org/records/8184043",
    source_doi="10.1038/s41467-023-40629-8",
    notes=(
        "Weighted mean of 14 published run gradients; statistical uncertainty "
        "combined with the reported 2.5e-19/cm systematic uncertainty. "
        "Runs share one apparatus and are not 14 independent experiments."
    ),
)

# Chou et al. report a 4.1(1.6)e-17 net frequency change after raising one
# optical clock by 33 cm. The 33 cm displacement is the experimental input.
_CHOU_REFERENCE = G_LOCAL_M_S2 * 0.33 / (C_M_S**2)
CHOU_2010_HOLDOUT = ClockBenchmark(
    name="Chou et al. 2010, 33 cm optical-clock height change",
    height_equivalent_m=0.33,
    observed_fractional_shift=4.1e-17,
    observed_sigma=1.6e-17,
    reference_fractional_shift=_CHOU_REFERENCE,
    role="INDEPENDENT_HOLDOUT",
    source_url="https://www.nist.gov/publications/relativity-and-optical-clocks",
    source_doi="10.1126/science.1192720",
    notes=(
        "Reported net shift after raising a clock by 33 cm; approximately "
        "4.1 +/- 1.6e-17. The reference shift is calculated from local g and height."
    ),
)

# PTB's 2025 dataset reports an independent geodetic geopotential difference
# and the clock-derived geopotential difference. The geodetic value is the
# spatial input; the clock result is the target output.
PTB_2025_GEODETIC_POTENTIAL_M2_S2 = 3915.88
PTB_2025_GEODETIC_SIGMA_M2_S2 = 0.30
PTB_2025_CLOCK_POTENTIAL_M2_S2 = 3918.1
PTB_2025_CLOCK_SIGMA_M2_S2 = 2.6
_PTB_HEIGHT = PTB_2025_GEODETIC_POTENTIAL_M2_S2 / G_LOCAL_M_S2
_PTB_OBSERVED = PTB_2025_CLOCK_POTENTIAL_M2_S2 / (C_M_S**2)
_PTB_SIGMA = sqrt(
    PTB_2025_CLOCK_SIGMA_M2_S2**2 + PTB_2025_GEODETIC_SIGMA_M2_S2**2
) / (C_M_S**2)
_PTB_REFERENCE = PTB_2025_GEODETIC_POTENTIAL_M2_S2 / (C_M_S**2)
PTB_2025_CALIBRATION = ClockBenchmark(
    name="Grotti et al. 2024/2025, 457 km chronometric levelling",
    height_equivalent_m=_PTB_HEIGHT,
    observed_fractional_shift=_PTB_OBSERVED,
    observed_sigma=_PTB_SIGMA,
    reference_fractional_shift=_PTB_REFERENCE,
    role="EXTERNAL_CALIBRATION",
    source_url="https://oar.ptb.de/resources/show/10.7795/720.20250315",
    source_doi="10.1103/PhysRevApplied.21.L061001",
    notes=(
        "The coordinate is an equivalent height derived from independently "
        "measured geodetic geopotential, not the 457 km horizontal distance. "
        "Clock and geodetic uncertainties are combined in quadrature."
    ),
)
