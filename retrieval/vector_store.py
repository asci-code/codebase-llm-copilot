from __future__ import annotations

from typing import Iterable

import chromadb
from chromadb.api.models.Collection import Collection

from app.config import settings
from ingestion.types import DocumentChunk
from retrieval.embeddings import EmbeddingProvider


class VectorStore:
    def __init__(self, provider: EmbeddingProvider) -> None:
        self.client = chromadb.PersistentClient(path=settings.chroma_dir)
        self.provider = provider

    def get_collection(self, repo_id: str) -> Collection:
        return self.client.get_or_create_collection(name=f"repo_{repo_id}")

    def upsert(self, repo_id: str, chunks: Iterable[DocumentChunk]) -> None:
        collection = self.get_collection(repo_id)
        chunks_list = list(chunks)
        if not chunks_list:
            return
        embeddings = self.provider.embed([chunk.content for chunk in chunks_list])
        collection.upsert(
            ids=[chunk.chunk_id for chunk in chunks_list],
            embeddings=embeddings,
            documents=[chunk.content for chunk in chunks_list],
            metadatas=[
                {
                    "path": chunk.path,
                    "start_line": chunk.start_line,
                    "end_line": chunk.end_line,
                    "language": chunk.language,
                    "symbols": ",".join(chunk.symbols),
                    "imports": ",".join(chunk.imports),
                    "module": chunk.module,
                    "repo_id": chunk.repo_id,
                }
                for chunk in chunks_list
            ],
        )

    def search(self, repo_id: str, query: str, top_k: int) -> list[dict]:
        collection = self.get_collection(repo_id)
        embedding = self.provider.embed([query])[0]
        results = collection.query(
            query_embeddings=[embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances", "ids"],
        )
        hits = []
        for idx, doc_id in enumerate(results["ids"][0]):
            hits.append(
                {
                    "id": doc_id,
                    "document": results["documents"][0][idx],
                    "metadata": results["metadatas"][0][idx],
                    "distance": results["distances"][0][idx],
                }
            )
        return hits

    def fetch_by_module(self, repo_id: str, module: str, limit: int = 5) -> list[dict]:
        collection = self.get_collection(repo_id)
        results = collection.get(
            where={"module": module, "repo_id": repo_id},
            include=["documents", "metadatas", "ids"],
            limit=limit,
        )
        hits = []
        for idx, doc_id in enumerate(results["ids"]):
            hits.append(
                {
                    "id": doc_id,
                    "document": results["documents"][idx],
                    "metadata": results["metadatas"][idx],
                    "distance": None,
                }
            )
        return hits
