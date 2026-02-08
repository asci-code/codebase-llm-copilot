from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence

from app.config import settings


class EmbeddingProvider(ABC):
    @abstractmethod
    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        raise NotImplementedError


class LocalSentenceEmbedding(EmbeddingProvider):
    def __init__(self) -> None:
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        return self.model.encode(list(texts), show_progress_bar=False).tolist()


class OpenAIEmbedding(EmbeddingProvider):
    def __init__(self, api_key: str) -> None:
        from openai import OpenAI

        self.client = OpenAI(api_key=api_key)

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        response = self.client.embeddings.create(
            model="text-embedding-3-small", input=list(texts)
        )
        return [item.embedding for item in response.data]


def build_embedding_provider() -> EmbeddingProvider:
    if settings.embedding_provider == "openai" and settings.openai_api_key:
        return OpenAIEmbedding(settings.openai_api_key)
    return LocalSentenceEmbedding()
