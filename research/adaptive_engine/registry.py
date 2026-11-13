"""Portable JSON registry for reproducible model configurations."""
from __future__ import annotations
from dataclasses import asdict, dataclass
import json
from pathlib import Path
from .optimizer import Candidate
from .stability import StabilityReport

@dataclass(frozen=True)
class ModelRecord:
    name: str
    candidate: Candidate
    stability: StabilityReport
    metadata: dict[str, str]

class ModelRegistry:
    def __init__(self):
        self._records: dict[str, ModelRecord] = {}

    def save(self, record: ModelRecord) -> None:
        if not record.name.strip():
            raise ValueError("record name is required")
        self._records[record.name] = record

    def get(self, name: str) -> ModelRecord:
        return self._records[name]

    def records(self) -> tuple[ModelRecord, ...]:
        return tuple(sorted(self._records.values(), key=lambda r: (r.candidate.score, r.name)))

    def export_json(self, path: str | Path) -> None:
        payload = []
        for record in self.records():
            payload.append({
                "name": record.name, "candidate": asdict(record.candidate),
                "stability": asdict(record.stability), "metadata": record.metadata,
            })
        Path(path).write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    def load_json(self, path: str | Path) -> None:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        for item in payload:
            c = item["candidate"]; s = item["stability"]
            self.save(ModelRecord(item["name"], Candidate(**c), StabilityReport(**s), item["metadata"]))
