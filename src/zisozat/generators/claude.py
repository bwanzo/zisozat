"""Claude (Anthropic) generator."""

from __future__ import annotations

try:
    import anthropic as anthropic
except ImportError:
    anthropic = None  # type: ignore[assignment]

from .base import BaseGenerator

_DEFAULT_MODEL = "claude-opus-4-5"
_DEFAULT_MAX_TOKENS = 4096


class ClaudeGenerator(BaseGenerator):
    """Generates decision trees using the Anthropic Claude API."""

    provider_name = "claude"

    def __init__(
        self,
        api_key: str | None = None,
        model: str = _DEFAULT_MODEL,
        max_tokens: int = _DEFAULT_MAX_TOKENS,
    ) -> None:
        super().__init__(model=model)
        if anthropic is None:
            raise ImportError(
                "The 'anthropic' package is required for the Claude provider. "
                "Install it with: pip install anthropic"
            )

        self._client = anthropic.Anthropic(api_key=api_key)
        self._max_tokens = max_tokens

    def _call_api(self, topic: str) -> str:
        response = self._client.messages.create(
            model=self.model,
            max_tokens=self._max_tokens,
            system=self._system_prompt,
            messages=[{"role": "user", "content": self._user_prompt(topic)}],
        )
        return response.content[0].text
