from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class DocumentChunk:
    chunk_id: str
    repo_id: str
    path: str
    content: str
    start_line: int
    end_line: int
    language: str
    symbols: list[str] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def module(self) -> str:
        module = self.path.replace("/", ".")
        for suffix in (".py", ".js", ".ts", ".json", ".yaml", ".yml", ".md"):
            if module.endswith(suffix):
                module = module[: -len(suffix)]
                break
        return module
