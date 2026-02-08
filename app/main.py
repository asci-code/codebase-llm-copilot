from __future__ import annotations

import time
from pathlib import Path

import networkx as nx
from fastapi import FastAPI, HTTPException

from agent.agent import CopilotAgent
from agent.observability import TraceStore
from app.config import settings
from app.schemas import AskRequest, AskResponse, IngestRequest, IngestResponse, TraceResponse
from graph.builder import build_graph
from ingestion.ingest import ingest_repo
from retrieval.embeddings import build_embedding_provider
from retrieval.retriever import HybridRetriever
from retrieval.vector_store import VectorStore

app = FastAPI(title=settings.app_name)

_embedding_provider = build_embedding_provider()
_vector_store = VectorStore(_embedding_provider)
_graph_cache: dict[str, nx.DiGraph] = {}


def _get_agent(repo_id: str) -> CopilotAgent:
    graph = _graph_cache.get(repo_id)
    if graph is None:
        raise HTTPException(status_code=404, detail="Repo not ingested")
    retriever = HybridRetriever(_vector_store, graph)
    return CopilotAgent(retriever)


@app.post("/ingest", response_model=IngestResponse)
async def ingest(request: IngestRequest) -> IngestResponse:
    start_time = time.time()
    repo_id, repo_path, chunks = ingest_repo(request.repo_url)
    _vector_store.upsert(repo_id, chunks)
    graph = build_graph(Path(repo_path))
    _graph_cache[repo_id] = graph
    latency = time.time() - start_time
    return IngestResponse(repo_id=repo_id, indexed_chunks=len(chunks))


@app.post("/ask", response_model=AskResponse)
async def ask(request: AskRequest) -> AskResponse:
    agent = _get_agent(request.repo_id)
    answer = agent.answer_question(request.repo_id, request.question)
    return AskResponse(
        answer=answer.answer,
        citations=answer.citations,
        confidence=answer.confidence,
        trace_id=answer.trace_id,
    )


@app.get("/trace/{trace_id}", response_model=TraceResponse)
async def trace(trace_id: str) -> TraceResponse:
    store = TraceStore()
    try:
        trace_data = store.load(trace_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Trace not found")
    return TraceResponse(trace=trace_data)


def run() -> None:
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    run()
