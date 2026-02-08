from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Iterable

from app.config import settings
from ingestion.types import DocumentChunk

SUPPORTED_EXTENSIONS = {".py", ".ts", ".js", ".md", ".json", ".yaml", ".yml"}


class PythonAnalyzer(ast.NodeVisitor):
    def __init__(self) -> None:
        self.symbols: list[str] = []
        self.imports: list[str] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.symbols.append(node.name)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.symbols.append(node.name)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.symbols.append(node.name)
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.imports.append(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module:
            self.imports.append(node.module)
        self.generic_visit(node)


def _python_chunks(content: str, path: str, repo_id: str) -> list[DocumentChunk]:
    tree = ast.parse(content)
    analyzer = PythonAnalyzer()
    analyzer.visit(tree)

    lines = content.splitlines()
    chunks: list[DocumentChunk] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            start = node.lineno
            end = node.end_lineno or node.lineno
            chunk_content = "\n".join(lines[start - 1 : end])
            chunk_id = f"{repo_id}:{path}:{start}-{end}"
            chunks.append(
                DocumentChunk(
                    chunk_id=chunk_id,
                    repo_id=repo_id,
                    path=path,
                    content=chunk_content,
                    start_line=start,
                    end_line=end,
                    language="python",
                    symbols=[node.name],
                    imports=analyzer.imports,
                    metadata={"type": type(node).__name__},
                )
            )
    if not chunks:
        chunk_id = f"{repo_id}:{path}:1-{len(lines)}"
        chunks.append(
            DocumentChunk(
                chunk_id=chunk_id,
                repo_id=repo_id,
                path=path,
                content=content,
                start_line=1,
                end_line=len(lines),
                language="python",
                symbols=analyzer.symbols,
                imports=analyzer.imports,
            )
        )
    return chunks


def _regex_symbols(pattern: str, content: str) -> list[str]:
    return re.findall(pattern, content)


def _generic_chunks(
    content: str, path: str, repo_id: str, language: str
) -> list[DocumentChunk]:
    lines = content.splitlines()
    chunks: list[DocumentChunk] = []
    total_lines = len(lines)
    max_lines = max(20, settings.chunk_size // 4)
    for start in range(0, total_lines, max_lines):
        end = min(start + max_lines, total_lines)
        chunk_content = "\n".join(lines[start:end])
        chunk_id = f"{repo_id}:{path}:{start + 1}-{end}"
        chunks.append(
            DocumentChunk(
                chunk_id=chunk_id,
                repo_id=repo_id,
                path=path,
                content=chunk_content,
                start_line=start + 1,
                end_line=end,
                language=language,
            )
        )
    return chunks


def parse_file(path: Path, repo_root: Path, repo_id: str) -> list[DocumentChunk]:
    relative = path.relative_to(repo_root).as_posix()
    content = path.read_text(encoding="utf-8", errors="ignore")
    suffix = path.suffix.lower()
    if suffix == ".py":
        return _python_chunks(content, relative, repo_id)
    if suffix in {".ts", ".js"}:
        symbols = _regex_symbols(r"(?:function|class)\s+([A-Za-z0-9_]+)", content)
        imports = _regex_symbols(r"from\s+['\"]([^'\"]+)['\"]", content)
        chunks = _generic_chunks(content, relative, repo_id, "javascript")
        for chunk in chunks:
            chunk.symbols = symbols
            chunk.imports = imports
        return chunks
    if suffix in {".yaml", ".yml"}:
        return _generic_chunks(content, relative, repo_id, "yaml")
    if suffix == ".json":
        return _generic_chunks(content, relative, repo_id, "json")
    if suffix == ".md":
        return _generic_chunks(content, relative, repo_id, "markdown")
    return []


def iter_source_files(repo_root: Path) -> Iterable[Path]:
    for path in repo_root.rglob("*"):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            if ".git" not in path.parts:
                yield path
