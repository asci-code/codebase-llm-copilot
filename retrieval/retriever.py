from __future__ import annotations

from dataclasses import dataclass

import networkx as nx

from app.config import settings
from retrieval.vector_store import VectorStore


@dataclass(slots=True)
class RetrievalResult:
    content: str
    metadata: dict
    score: float


class HybridRetriever:
    def __init__(self, vector_store: VectorStore, graph: nx.DiGraph) -> None:
        self.vector_store = vector_store
        self.graph = graph

    def retrieve(self, repo_id: str, query: str) -> list[RetrievalResult]:
        hits = self.vector_store.search(repo_id, query, settings.max_results)
        results: list[RetrievalResult] = []
        for hit in hits:
            score = 1.0 / (1.0 + hit["distance"]) if hit["distance"] is not None else 0.0
            results.append(
                RetrievalResult(
                    content=hit["document"], metadata=hit["metadata"], score=score
                )
            )
        expanded = self._expand_with_graph(repo_id, results)
        return sorted(expanded, key=lambda item: item.score, reverse=True)

    def _expand_with_graph(
        self, repo_id: str, results: list[RetrievalResult]
    ) -> list[RetrievalResult]:
        expanded = list(results)
        modules = {item.metadata.get("module") for item in results if item.metadata.get("module")}
        for module in modules:
            if module not in self.graph:
                continue
            neighbors = nx.single_source_shortest_path_length(
                self.graph, module, cutoff=settings.graph_neighbor_hops
            )
            for neighbor in neighbors:
                if neighbor == module:
                    continue
                for hit in self.vector_store.fetch_by_module(repo_id, neighbor, limit=2):
                    expanded.append(
                        RetrievalResult(
                            content=hit["document"],
                            metadata=hit["metadata"],
                            score=0.4,
                        )
                    )
        return expanded
