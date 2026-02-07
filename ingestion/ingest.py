from __future__ import annotations

from pathlib import Path

from ingestion.parser import iter_source_files, parse_file
from ingestion.repo import clone_repo
from ingestion.types import DocumentChunk


def ingest_repo(repo_url: str) -> tuple[str, Path, list[DocumentChunk]]:
    repo_id, repo_path = clone_repo(repo_url)
    chunks: list[DocumentChunk] = []
    for file_path in iter_source_files(repo_path):
        chunks.extend(parse_file(file_path, repo_path, repo_id))
    return repo_id, repo_path, chunks
