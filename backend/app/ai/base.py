from abc import ABC, abstractmethod


class AIProvider(ABC):
    """Minimal contract every LLM provider implements: prompt in, raw text out.

    Parsing, validation, and retry are deliberately NOT part of this contract
    — they are provider-agnostic concerns handled once, outside any provider
    implementation (see `app.features.extraction.parser` and
    `app.ai.retry`), so adding a new provider (OpenAI, Claude, Groq, Ollama,
    ...) never touches business logic.
    """

    @abstractmethod
    async def generate(self, prompt: str) -> str:
        """Send `prompt` to the underlying model and return its raw text response."""
        raise NotImplementedError
