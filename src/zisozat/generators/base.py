"""Abstract base class for AI decision-tree generators."""

from __future__ import annotations

import json
import textwrap
from abc import ABC, abstractmethod

from zisozat.models import DecisionTree

# ---------------------------------------------------------------------------
# Shared prompt template
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = textwrap.dedent(
    """\
    You are a decision-tree expert.
    Given a topic or question, you will produce a structured decision tree that
    helps the user reach a well-reasoned conclusion through a series of clear
    yes/no or multiple-choice questions.

    Rules:
    - Each non-leaf node must have exactly the options listed in its "options" array.
    - Each entry in "children" must map an option string to an existing node id.
    - Leaf nodes have an empty "options" array and a non-empty "conclusion" field.
    - Node ids must be unique strings (e.g. "n1", "n2", …).
    - Return ONLY valid JSON – no markdown fences, no explanation.

    JSON schema:
    {
      "title": "<tree title>",
      "description": "<one-sentence description>",
      "root_id": "<id of root node>",
      "provider": "<provider name>",
      "model": "<model name>",
      "nodes": {
        "<id>": {
          "id": "<id>",
          "question": "<question text>",
          "options": ["<option1>", "<option2>", ...],
          "children": {"<option1>": "<child_id>", "<option2>": "<child_id>", ...},
          "conclusion": null,
          "metadata": {}
        }
      }
    }

    Leaf node example:
    {
      "id": "n99",
      "question": "",
      "options": [],
      "children": {},
      "conclusion": "<recommendation text>",
      "metadata": {}
    }
    """
)


class BaseGenerator(ABC):
    """Abstract generator: subclasses implement :meth:`generate`."""

    #: Human-readable provider name stored in generated trees.
    provider_name: str = "base"

    def __init__(self, model: str) -> None:
        self.model = model

    @abstractmethod
    def _call_api(self, topic: str) -> str:
        """Call the AI API and return the raw text response."""

    def generate(self, topic: str) -> DecisionTree:
        """Generate a :class:`~zisozat.models.DecisionTree` for *topic*.

        Raises
        ------
        ValueError
            If the model returns malformed JSON or a structurally invalid tree.
        """
        raw = self._call_api(topic)
        return self._parse(raw)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @property
    def _system_prompt(self) -> str:
        return _SYSTEM_PROMPT

    def _user_prompt(self, topic: str) -> str:
        return (
            f"Generate a decision tree for the following topic:\n\n{topic}\n\n"
            "Return ONLY the JSON object described in the system prompt."
        )

    def _parse(self, raw: str) -> DecisionTree:
        """Parse *raw* JSON into a validated :class:`DecisionTree`."""
        raw = raw.strip()
        # Strip accidental markdown fences that some models add anyway
        if raw.startswith("```"):
            lines = raw.splitlines()
            raw = "\n".join(
                line for line in lines if not line.startswith("```")
            ).strip()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Model returned invalid JSON: {exc}\n\nRaw:\n{raw}") from exc

        # Inject provider/model if missing
        data.setdefault("provider", self.provider_name)
        data.setdefault("model", self.model)

        try:
            tree = DecisionTree.model_validate(data)
        except Exception as exc:
            raise ValueError(f"Decision tree validation failed: {exc}") from exc

        self._validate_tree(tree)
        return tree

    @staticmethod
    def _validate_tree(tree: DecisionTree) -> None:
        """Check that all child references point to existing nodes."""
        for node in tree.nodes.values():
            for option, child_id in node.children.items():
                if child_id not in tree.nodes:
                    raise ValueError(
                        f"Node '{node.id}' option '{option}' references "
                        f"unknown child '{child_id}'."
                    )
        if tree.root_id not in tree.nodes:
            raise ValueError(f"Root id '{tree.root_id}' not found in nodes.")
