from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path
from typing import Tuple

from app.config import settings


def _safe_repo_name(repo_url: str) -> str:
    hashed = hashlib.sha256(repo_url.encode("utf-8")).hexdigest()[:10]
    name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")
    return f"{name}-{hashed}"


def clone_repo(repo_url: str) -> Tuple[str, Path]:
    repo_name = _safe_repo_name(repo_url)
    base_dir = Path(settings.data_dir) / "repos"
    base_dir.mkdir(parents=True, exist_ok=True)
    repo_path = base_dir / repo_name
    if repo_path.exists():
        return repo_name, repo_path
    result = subprocess.run(
        ["git", "clone", "--depth", "1", repo_url, str(repo_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Failed to clone repo: {result.stderr.strip()}")
    return repo_name, repo_path
