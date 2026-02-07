from __future__ import annotations

import time
from dataclasses import dataclass

from agent.llm import LLMProvider, build_llm
from agent.observability import Trace, TraceStore
from app.config import settings
from retrieval.retriever import HybridRetriever


@dataclass
class Answer:
    answer: str
    citations: list[dict]
    confidence: float
    trace_id: str


class CopilotAgent:
    def __init__(self, retriever: HybridRetriever) -> None:
        self.retriever = retriever
        self.llm: LLMProvider = build_llm()
        self.trace_store = TraceStore()

    def answer_question(self, repo_id: str, question: str) -> Answer:
        plan = self._plan(question)
        start_time = time.time()
        retrieved = self.retriever.retrieve(repo_id, question)
        retrieval_time = time.time() - start_time
        analysis_prompt, citations = self._build_analysis_prompt(question, retrieved)
        answer_text = self.llm.generate(self._system_prompt(), analysis_prompt)
        confidence = self._confidence(retrieved)
        trace_id = self.trace_store.new_trace_id()
        trace = Trace(
            trace_id=trace_id,
            question=question,
            plan=plan,
            retrieved=[
                {
                    "metadata": item.metadata,
                    "score": item.score,
                    "content": item.content,
                }
                for item in retrieved
            ],
            answer=answer_text,
            confidence=confidence,
            timings={"retrieval_s": retrieval_time},
            token_usage={},
        )
        self.trace_store.save(trace)
        return Answer(answer=answer_text, citations=citations, confidence=confidence, trace_id=trace_id)

    def _plan(self, question: str) -> str:
        return (
            "Plan: (1) locate relevant modules via semantic + graph retrieval, "
            "(2) analyze key architectural flows, (3) answer with citations."
        )

    def _system_prompt(self) -> str:
        return (
            "You are a senior software architect. Use the provided context to answer. "
            "Cite file paths and line ranges. Be concise but specific."
        )

    def _build_analysis_prompt(self, question: str, retrieved: list) -> tuple[str, list[dict]]:
        context_lines = []
        citations: list[dict] = []
        for idx, item in enumerate(retrieved, start=1):
            metadata = item.metadata
            context_lines.append(
                f"[{idx}] {metadata.get('path')}:{metadata.get('start_line')}-{metadata.get('end_line')}\n"
                f"{item.content}"
            )
            citations.append(
                {
                    "index": idx,
                    "path": metadata.get("path"),
                    "start_line": metadata.get("start_line"),
                    "end_line": metadata.get("end_line"),
                    "score": item.score,
                }
            )
        context = "\n\n".join(context_lines)
        prompt = (
            f"Question: {question}\n\n"
            "Context:\n"
            f"{context}\n\n"
            "Answer with citations in the format [index]."
        )
        return prompt, citations

    def _confidence(self, retrieved: list) -> float:
        if not retrieved:
            return 0.0
        avg = sum(item.score for item in retrieved) / len(retrieved)
        return round(min(1.0, avg), 2)
