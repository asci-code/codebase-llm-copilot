from __future__ import annotations

import json
import statistics
from pathlib import Path

import httpx
from rich import print

API_URL = "http://localhost:8000"


def load_questions() -> list[dict]:
    path = Path(__file__).with_name("questions.json")
    return json.loads(path.read_text(encoding="utf-8"))


def has_valid_citations(citations: list[dict]) -> bool:
    return all(
        citation.get("path") and citation.get("start_line") and citation.get("end_line")
        for citation in citations
    )


def eval_repo(repo_url: str) -> None:
    questions = load_questions()
    with httpx.Client(timeout=60.0) as client:
        ingest_resp = client.post(f"{API_URL}/ingest", json={"repo_url": repo_url})
        ingest_resp.raise_for_status()
        repo_id = ingest_resp.json()["repo_id"]
        scores = []
        for item in questions:
            ask_resp = client.post(
                f"{API_URL}/ask", json={"repo_id": repo_id, "question": item["question"]}
            )
            ask_resp.raise_for_status()
            payload = ask_resp.json()
            citations_ok = has_valid_citations(payload["citations"])
            keyword_hits = sum(
                1 for keyword in item["expected_keywords"] if keyword in payload["answer"].lower()
            )
            score = 0.5 * (keyword_hits / len(item["expected_keywords"])) + 0.5 * (
                1.0 if citations_ok else 0.0
            )
            scores.append(score)
            print(
                {
                    "question": item["question"],
                    "score": round(score, 2),
                    "citations_ok": citations_ok,
                }
            )
        print({"avg_score": round(statistics.mean(scores), 2)})


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Evaluate the copilot agent.")
    parser.add_argument("repo_url", help="GitHub repository URL to ingest")
    args = parser.parse_args()
    eval_repo(args.repo_url)
