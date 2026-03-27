"""Interactive decision tree runner."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import DecisionNode, DecisionTree


class TreeRunner:
    """Traverses a :class:`~zisozat.models.DecisionTree` step by step.

    The runner is deliberately I/O-free so it can be driven by any
    front-end (CLI, web, tests …).
    """

    def __init__(self, tree: "DecisionTree") -> None:
        self.tree = tree
        self._current_id: str = tree.root_id
        self._history: list[tuple[str, str]] = []  # (node_id, chosen_option)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    @property
    def current_node(self) -> "DecisionNode":
        return self.tree.get_node(self._current_id)

    @property
    def is_done(self) -> bool:
        """Return *True* when the current node is a leaf (conclusion)."""
        node = self.current_node
        return not node.options

    @property
    def history(self) -> list[tuple[str, str]]:
        return list(self._history)

    def choose(self, option: str) -> "DecisionNode":
        """Apply *option* to the current node and advance to the next.

        Returns the new current node.

        Raises
        ------
        ValueError
            If *option* is not one of the valid choices, or if the tree
            is already at a leaf.
        """
        node = self.current_node
        if self.is_done:
            raise ValueError("The decision tree has already reached a conclusion.")
        if option not in node.children:
            valid = ", ".join(f"'{o}'" for o in node.options)
            raise ValueError(
                f"Invalid option '{option}'. Valid options are: {valid}"
            )
        self._history.append((self._current_id, option))
        self._current_id = node.children[option]
        return self.current_node

    def reset(self) -> None:
        """Return to the root node."""
        self._current_id = self.tree.root_id
        self._history.clear()
