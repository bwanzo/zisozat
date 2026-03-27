"""AI generator package."""

from .base import BaseGenerator
from .claude import ClaudeGenerator
from .openai import OpenAIGenerator

__all__ = ["BaseGenerator", "ClaudeGenerator", "OpenAIGenerator"]


def get_generator(provider: str, **kwargs: object) -> BaseGenerator:
    """Return the appropriate generator for *provider*.

    Parameters
    ----------
    provider:
        ``"claude"`` or ``"openai"``.
    **kwargs:
        Forwarded to the generator constructor (e.g. ``api_key``, ``model``).
    """
    mapping = {
        "claude": ClaudeGenerator,
        "openai": OpenAIGenerator,
    }
    key = provider.lower()
    if key not in mapping:
        raise ValueError(
            f"Unknown provider '{provider}'. Supported providers: {', '.join(mapping)}."
        )
    return mapping[key](**kwargs)  # type: ignore[arg-type]
