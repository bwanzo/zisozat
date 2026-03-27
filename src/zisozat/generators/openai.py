"""OpenAI generator."""

from __future__ import annotations

try:
    import openai as openai
except ImportError:
    openai = None  # type: ignore[assignment]

from .base import BaseGenerator

_DEFAULT_MODEL = "gpt-4o"
_DEFAULT_MAX_TOKENS = 4096


class OpenAIGenerator(BaseGenerator):
    """Generates decision trees using the OpenAI Chat Completions API."""

    provider_name = "openai"

    def __init__(
        self,
        api_key: str | None = None,
        model: str = _DEFAULT_MODEL,
        max_tokens: int = _DEFAULT_MAX_TOKENS,
    ) -> None:
        super().__init__(model=model)
        if openai is None:
            raise ImportError(
                "The 'openai' package is required for the OpenAI provider. "
                "Install it with: pip install openai"
            )

        self._client = openai.OpenAI(api_key=api_key)
        self._max_tokens = max_tokens

    def _call_api(self, topic: str) -> str:
        response = self._client.chat.completions.create(
            model=self.model,
            max_tokens=self._max_tokens,
            messages=[
                {"role": "system", "content": self._system_prompt},
                {"role": "user", "content": self._user_prompt(topic)},
            ],
            response_format={"type": "json_object"},
        )
        return response.choices[0].message.content or ""
