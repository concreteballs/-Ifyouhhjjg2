"""Published gravitational-redshift benchmark values.

Values are absolute fractional frequency shifts. x is the published
reference-predicted shift and y is the reported measured shift.
"""
from .model import RedshiftObservation

PUBLISHED_BENCHMARKS = (
    RedshiftObservation(
        name="Pound-Rebka 22.5 m tower (two-way differential)",
        x=4.885e-15, y=5.13e-15, sigma=0.51e-15,
        input_kind="reference_potential_shift",
        source="Pound-Rebka measurement; value and reference prediction reproduced in a later analysis",
        source_url="https://paulba.no/pdf/PoundRebka.pdf",
        source_doi="10.1103/PhysRevLett.4.337",
        notes="The reported comparison is the total top/bottom reversal signal, not a one-way shift.",
    ),
    RedshiftObservation(
        name="Zheng et al. 2023 optical-clock gradient (1 cm)",
        x=10.9e-19, y=12.4e-19, sigma=2.6e-19,
        input_kind="reference_potential_shift",
        source="Nature Communications 14, 4886 (2023), corrected weighted-mean gradient",
        source_url="https://pmc.ncbi.nlm.nih.gov/articles/PMC10423269/",
        source_doi="10.1038/s41467-023-40629-8",
        notes="Magnitude for a 1 cm separation. Combined uncertainty approximately 2.6e-19/cm from 0.7 statistical and 2.5 systematic.",
    ),
)

def benchmark_summary() -> dict[str, object]:
    return {
        "count": len(PUBLISHED_BENCHMARKS),
        "independent_raw_points": False,
        "input_kind": "reference_potential_shift",
        "warning": "Aggregate results from two experiments; not raw-data fit and not a TIK-flow measurement.",
        "experiments": [
            {"name": item.name, "reference_shift": item.x, "measured_shift": item.y,
             "uncertainty": item.sigma, "source_url": item.source_url, "source_doi": item.source_doi}
            for item in PUBLISHED_BENCHMARKS
        ],
    }
