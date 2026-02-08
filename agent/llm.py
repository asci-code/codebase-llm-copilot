from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence

from app.config import settings


class LLMProvider(ABC):
    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        raise NotImplementedError


class SimpleLLM(LLMProvider):
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        return (
            "I do not have access to a generative model in this environment. "
            "Below is a structured, extractive response based on retrieved context.\n\n"
            f"{user_prompt}"
        )


class OpenAIChatLLM(LLMProvider):
    def __init__(self, api_key: str) -> None:
        from openai import OpenAI

        self.client = OpenAI(api_key=api_key)

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.choices[0].message.content


def build_llm() -> LLMProvider:
    if settings.llm_provider == "openai" and settings.openai_api_key:
        return OpenAIChatLLM(settings.openai_api_key)
    return SimpleLLM()
