from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    app_name: str = "codebase-llm-copilot"
    data_dir: str = Field(default="data", alias="DATA_DIR")
    chroma_dir: str = Field(default="data/chroma", alias="CHROMA_DIR")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    embedding_provider: str = Field(default="local", alias="EMBEDDING_PROVIDER")
    llm_provider: str = Field(default="simple", alias="LLM_PROVIDER")
    chunk_size: int = Field(default=800, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=100, alias="CHUNK_OVERLAP")
    max_results: int = Field(default=8, alias="MAX_RESULTS")
    graph_neighbor_hops: int = Field(default=1, alias="GRAPH_NEIGHBOR_HOPS")


settings = Settings()
