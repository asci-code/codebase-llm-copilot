from __future__ import annotations

from pathlib import Path
import re

import networkx as nx


def _to_module(path: Path, repo_root: Path) -> str:
    module = path.relative_to(repo_root).as_posix().replace("/", ".")
    for suffix in (".py", ".js", ".ts"):
        if module.endswith(suffix):
            return module[: -len(suffix)]
    return module


def build_graph(repo_root: Path) -> nx.DiGraph:
    graph = nx.DiGraph()
    for path in repo_root.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        if path.suffix.lower() not in {".py", ".ts", ".js"}:
            continue
        module = _to_module(path, repo_root)
        graph.add_node(module)
        content = path.read_text(encoding="utf-8", errors="ignore")
        if path.suffix.lower() == ".py":
            for match in re.findall(r"^\s*import\s+([\w\.]+)", content, re.MULTILINE):
                graph.add_edge(module, match)
            for match in re.findall(r"^\s*from\s+([\w\.]+)\s+import", content, re.MULTILINE):
                graph.add_edge(module, match)
        else:
            for match in re.findall(r"from\s+['\"]([^'\"]+)['\"]", content):
                graph.add_edge(module, match)
    return graph
