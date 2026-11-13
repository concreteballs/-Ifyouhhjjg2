"""Extensible named entities and parameter sets for adaptive models."""
from __future__ import annotations
from dataclasses import dataclass, field
from math import isfinite
from typing import Mapping

@dataclass(frozen=True)
class Entity:
    name: str
    value: float
    unit: str = "dimensionless"
    role: str = "parameter"
    bounds: tuple[float, float] | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self):
        if not self.name.strip() or not isfinite(self.value):
            raise ValueError("entity requires a name and finite value")
        if self.bounds is not None:
            low, high = self.bounds
            if not isfinite(low) or not isfinite(high) or low > high or not low <= self.value <= high:
                raise ValueError("entity value must lie within finite ordered bounds")

@dataclass(frozen=True)
class EntitySet:
    entities: tuple[Entity, ...]

    def __post_init__(self):
        names = [item.name for item in self.entities]
        if len(names) != len(set(names)):
            raise ValueError("entity names must be unique")

    def as_dict(self) -> dict[str, float]:
        return {item.name: item.value for item in self.entities}

    def replace_values(self, values: Mapping[str, float]) -> "EntitySet":
        unknown = set(values) - {item.name for item in self.entities}
        if unknown:
            raise ValueError("unknown entities: " + ", ".join(sorted(unknown)))
        return EntitySet(tuple(
            Entity(e.name, values.get(e.name, e.value), e.unit, e.role, e.bounds, e.metadata)
            for e in self.entities
        ))
