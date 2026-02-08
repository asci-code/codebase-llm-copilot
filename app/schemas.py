from __future__ import annotations

from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
    repo_url: str = Field(..., examples=["https://github.com/org/repo"])


class IngestResponse(BaseModel):
    repo_id: str
    indexed_chunks: int


class AskRequest(BaseModel):
    repo_id: str
    question: str


class AskResponse(BaseModel):
    answer: str
    citations: list[dict]
    confidence: float
    trace_id: str


class TraceResponse(BaseModel):
    trace: dict
