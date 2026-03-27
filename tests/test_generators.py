"""Tests for AI generators (no real API calls – everything is mocked)."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from zisozat.generators import get_generator
from zisozat.generators.base import BaseGenerator
from zisozat.models import DecisionTree

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_VALID_TREE_JSON = json.dumps(
    {
        "title": "Test tree",
        "description": "A simple test tree",
        "root_id": "n1",
        "provider": "test",
        "model": "test-model",
        "nodes": {
            "n1": {
                "id": "n1",
                "question": "Is it sunny?",
                "options": ["Yes", "No"],
                "children": {"Yes": "n2", "No": "n3"},
                "conclusion": None,
                "metadata": {},
            },
            "n2": {
                "id": "n2",
                "question": "",
                "options": [],
                "children": {},
                "conclusion": "Go outside!",
                "metadata": {},
            },
            "n3": {
                "id": "n3",
                "question": "",
                "options": [],
                "children": {},
                "conclusion": "Stay inside.",
                "metadata": {},
            },
        },
    }
)


# ---------------------------------------------------------------------------
# Concrete stub generator
# ---------------------------------------------------------------------------


class _StubGenerator(BaseGenerator):
    """Stub that returns a pre-baked JSON string."""

    provider_name = "stub"

    def __init__(self, response: str, model: str = "stub-model") -> None:
        super().__init__(model=model)
        self._response = response

    def _call_api(self, topic: str) -> str:
        return self._response


# ---------------------------------------------------------------------------
# BaseGenerator / _StubGenerator
# ---------------------------------------------------------------------------


class TestBaseGenerator:
    def test_generate_valid_tree(self):
        gen = _StubGenerator(_VALID_TREE_JSON)
        tree = gen.generate("test topic")
        assert isinstance(tree, DecisionTree)
        assert tree.title == "Test tree"
        assert tree.root_id == "n1"
        assert len(tree.nodes) == 3

    def test_strips_markdown_fences(self):
        fenced = f"```json\n{_VALID_TREE_JSON}\n```"
        gen = _StubGenerator(fenced)
        tree = gen.generate("test topic")
        assert isinstance(tree, DecisionTree)

    def test_invalid_json_raises(self):
        gen = _StubGenerator("not valid json {{{")
        with pytest.raises(ValueError, match="invalid JSON"):
            gen.generate("test topic")

    def test_broken_child_reference_raises(self):
        data = json.loads(_VALID_TREE_JSON)
        data["nodes"]["n1"]["children"]["Yes"] = "nonexistent"
        gen = _StubGenerator(json.dumps(data))
        with pytest.raises(ValueError, match="unknown child"):
            gen.generate("test topic")

    def test_missing_root_raises(self):
        data = json.loads(_VALID_TREE_JSON)
        data["root_id"] = "ghost"
        gen = _StubGenerator(json.dumps(data))
        with pytest.raises(ValueError, match="Root id"):
            gen.generate("test topic")


# ---------------------------------------------------------------------------
# get_generator factory
# ---------------------------------------------------------------------------


class TestGetGenerator:
    def test_unknown_provider_raises(self):
        with pytest.raises(ValueError, match="Unknown provider"):
            get_generator("gemini")

    @patch("zisozat.generators.claude.anthropic")
    def test_claude_generator_created(self, mock_anthropic):
        mock_anthropic.Anthropic.return_value = MagicMock()
        gen = get_generator("claude", api_key="test-key")
        from zisozat.generators.claude import ClaudeGenerator
        assert isinstance(gen, ClaudeGenerator)

    @patch("zisozat.generators.openai.openai")
    def test_openai_generator_created(self, mock_openai):
        mock_openai.OpenAI.return_value = MagicMock()
        gen = get_generator("openai", api_key="test-key")
        from zisozat.generators.openai import OpenAIGenerator
        assert isinstance(gen, OpenAIGenerator)


# ---------------------------------------------------------------------------
# ClaudeGenerator (mocked)
# ---------------------------------------------------------------------------


class TestClaudeGenerator:
    @patch("zisozat.generators.claude.anthropic")
    def test_generate_calls_api(self, mock_anthropic):
        mock_client = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=_VALID_TREE_JSON)]
        mock_client.messages.create.return_value = mock_response

        from zisozat.generators.claude import ClaudeGenerator

        gen = ClaudeGenerator(api_key="test-key")
        tree = gen.generate("Should I adopt a dog?")
        assert isinstance(tree, DecisionTree)
        mock_client.messages.create.assert_called_once()

    @patch("zisozat.generators.claude.anthropic", new=None)
    def test_missing_anthropic_raises(self):
        """If anthropic is None (not installed), a helpful ImportError is raised."""
        from zisozat.generators.claude import ClaudeGenerator

        with pytest.raises(ImportError, match="anthropic"):
            ClaudeGenerator(api_key="x")


# ---------------------------------------------------------------------------
# OpenAIGenerator (mocked)
# ---------------------------------------------------------------------------


class TestOpenAIGenerator:
    @patch("zisozat.generators.openai.openai")
    def test_generate_calls_api(self, mock_openai):
        mock_client = MagicMock()
        mock_openai.OpenAI.return_value = mock_client
        mock_choice = MagicMock()
        mock_choice.message.content = _VALID_TREE_JSON
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response

        from zisozat.generators.openai import OpenAIGenerator

        gen = OpenAIGenerator(api_key="test-key")
        tree = gen.generate("Best cloud database?")
        assert isinstance(tree, DecisionTree)
        mock_client.chat.completions.create.assert_called_once()
