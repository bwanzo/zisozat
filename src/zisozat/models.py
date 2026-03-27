"""Data models for decision trees."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class DecisionNode(BaseModel):
    """A single node in the decision tree.

    Leaf nodes (no ``children``) carry a ``conclusion`` – the final
    recommendation reached when the user arrives at this node.
    """

    id: str
    question: str
    """The yes/no or multiple-choice question presented to the user."""

    options: list[str] = Field(default_factory=list)
    """Possible answers the user can choose from.

    When empty the node is treated as a *leaf* (conclusion node).
    """

    children: dict[str, str] = Field(default_factory=dict)
    """Maps each option string to the ``id`` of the child node."""

    conclusion: str | None = None
    """Final recommendation text (only set for leaf nodes)."""

    metadata: dict[str, Any] = Field(default_factory=dict)
    """Arbitrary extra data (e.g. rationale, confidence, sources)."""


class DecisionTree(BaseModel):
    """A complete decision tree with a named root node."""

    title: str
    description: str = ""
    root_id: str
    nodes: dict[str, DecisionNode]
    provider: str = "unknown"
    model: str = "unknown"

    # ------------------------------------------------------------------
    # Serialisation helpers
    # ------------------------------------------------------------------

    def to_json(self, indent: int = 2) -> str:
        return self.model_dump_json(indent=indent)

    @classmethod
    def from_json(cls, data: str | bytes) -> "DecisionTree":
        return cls.model_validate_json(data)

    def save(self, path: str | Path) -> None:
        Path(path).write_text(self.to_json(), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "DecisionTree":
        return cls.from_json(Path(path).read_text(encoding="utf-8"))

    # ------------------------------------------------------------------
    # Traversal helpers
    # ------------------------------------------------------------------

    def get_node(self, node_id: str) -> DecisionNode:
        try:
            return self.nodes[node_id]
        except KeyError as exc:
            raise KeyError(f"Node '{node_id}' not found in tree '{self.title}'.") from exc

    @property
    def root(self) -> DecisionNode:
        return self.get_node(self.root_id)
