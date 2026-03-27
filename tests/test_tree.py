"""Tests for TreeRunner."""

import pytest

from zisozat.models import DecisionNode, DecisionTree
from zisozat.tree import TreeRunner


@pytest.fixture()
def simple_tree() -> DecisionTree:
    return DecisionTree(
        title="Tech stack choice",
        description="Pick a backend language.",
        root_id="n1",
        provider="test",
        model="test",
        nodes={
            "n1": DecisionNode(
                id="n1",
                question="Do you need strong typing?",
                options=["Yes", "No"],
                children={"Yes": "n2", "No": "n3"},
            ),
            "n2": DecisionNode(
                id="n2",
                question="Are you comfortable with JVM?",
                options=["Yes", "No"],
                children={"Yes": "n4", "No": "n5"},
            ),
            "n3": DecisionNode(
                id="n3",
                question="",
                options=[],
                children={},
                conclusion="Go with Python.",
            ),
            "n4": DecisionNode(
                id="n4",
                question="",
                options=[],
                children={},
                conclusion="Go with Kotlin.",
            ),
            "n5": DecisionNode(
                id="n5",
                question="",
                options=[],
                children={},
                conclusion="Go with TypeScript.",
            ),
        },
    )


class TestTreeRunner:
    def test_starts_at_root(self, simple_tree: DecisionTree):
        runner = TreeRunner(simple_tree)
        assert runner.current_node.id == "n1"

    def test_is_done_false_at_root(self, simple_tree: DecisionTree):
        runner = TreeRunner(simple_tree)
        assert not runner.is_done

    def test_choose_advances(self, simple_tree: DecisionTree):
        runner = TreeRunner(simple_tree)
        next_node = runner.choose("No")
        assert next_node.id == "n3"
        assert runner.is_done

    def test_conclusion_reached(self, simple_tree: DecisionTree):
        runner = TreeRunner(simple_tree)
        runner.choose("No")
        assert runner.current_node.conclusion == "Go with Python."

    def test_deep_path(self, simple_tree: DecisionTree):
        runner = TreeRunner(simple_tree)
        runner.choose("Yes")
        assert runner.current_node.id == "n2"
        runner.choose("Yes")
        assert runner.current_node.conclusion == "Go with Kotlin."

    def test_history_recorded(self, simple_tree: DecisionTree):
        runner = TreeRunner(simple_tree)
        runner.choose("Yes")
        runner.choose("No")
        assert runner.history == [("n1", "Yes"), ("n2", "No")]

    def test_invalid_option_raises(self, simple_tree: DecisionTree):
        runner = TreeRunner(simple_tree)
        with pytest.raises(ValueError, match="Invalid option"):
            runner.choose("Maybe")

    def test_choose_on_leaf_raises(self, simple_tree: DecisionTree):
        runner = TreeRunner(simple_tree)
        runner.choose("No")
        with pytest.raises(ValueError, match="conclusion"):
            runner.choose("No")

    def test_reset(self, simple_tree: DecisionTree):
        runner = TreeRunner(simple_tree)
        runner.choose("Yes")
        runner.reset()
        assert runner.current_node.id == "n1"
        assert runner.history == []
