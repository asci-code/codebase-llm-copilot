from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from app.config import settings


@dataclass
class Trace:
    trace_id: str
    question: str
    plan: str
    retrieved: list[dict]
    answer: str
    confidence: float
    timings: dict[str, float]
    token_usage: dict[str, int] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)


class TraceStore:
    def __init__(self) -> None:
        self.trace_dir = Path(settings.data_dir) / "traces"
        self.trace_dir.mkdir(parents=True, exist_ok=True)

    def new_trace_id(self) -> str:
        return str(uuid.uuid4())

    def save(self, trace: Trace) -> None:
        path = self.trace_dir / f"{trace.trace_id}.json"
        with path.open("w", encoding="utf-8") as handle:
            json.dump(asdict(trace), handle, indent=2)

    def load(self, trace_id: str) -> dict[str, Any]:
        path = self.trace_dir / f"{trace_id}.json"
        if not path.exists():
            raise FileNotFoundError(trace_id)
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
