"""Tests for DecisionTree and DecisionNode models."""


import pytest

from zisozat.models import DecisionNode, DecisionTree

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def simple_tree() -> DecisionTree:
    """A minimal two-level tree: root → yes → leaf / no → leaf."""
    return DecisionTree(
        title="Dog adoption",
        description="Should you adopt a dog?",
        root_id="n1",
        provider="test",
        model="test",
        nodes={
            "n1": DecisionNode(
                id="n1",
                question="Do you have enough space at home?",
                options=["Yes", "No"],
                children={"Yes": "n2", "No": "n3"},
            ),
            "n2": DecisionNode(
                id="n2",
                question="",
                options=[],
                children={},
                conclusion="Great – you can adopt a dog!",
            ),
            "n3": DecisionNode(
                id="n3",
                question="",
                options=[],
                children={},
                conclusion="Consider a smaller pet first.",
            ),
        },
    )


# ---------------------------------------------------------------------------
# DecisionNode
# ---------------------------------------------------------------------------


class TestDecisionNode:
    def test_leaf_node_has_no_options(self):
        node = DecisionNode(id="leaf", question="", options=[], children={}, conclusion="Done")
        assert node.options == []
        assert node.conclusion == "Done"

    def test_non_leaf_has_options(self):
        node = DecisionNode(
            id="n1",
            question="Question?",
            options=["Yes", "No"],
            children={"Yes": "n2", "No": "n3"},
        )
        assert len(node.options) == 2
        assert node.conclusion is None


# ---------------------------------------------------------------------------
# DecisionTree
# ---------------------------------------------------------------------------


class TestDecisionTree:
    def test_root_property(self, simple_tree: DecisionTree):
        root = simple_tree.root
        assert root.id == "n1"

    def test_get_node(self, simple_tree: DecisionTree):
        node = simple_tree.get_node("n2")
        assert node.conclusion == "Great – you can adopt a dog!"

    def test_get_node_missing_raises(self, simple_tree: DecisionTree):
        with pytest.raises(KeyError, match="not found"):
            simple_tree.get_node("missing")

    def test_json_roundtrip(self, simple_tree: DecisionTree):
        serialised = simple_tree.to_json()
        restored = DecisionTree.from_json(serialised)
        assert restored.title == simple_tree.title
        assert restored.root_id == simple_tree.root_id
        assert set(restored.nodes.keys()) == set(simple_tree.nodes.keys())

    def test_save_and_load(self, simple_tree: DecisionTree, tmp_path):
        path = tmp_path / "tree.json"
        simple_tree.save(path)
        loaded = DecisionTree.load(path)
        assert loaded.title == simple_tree.title
        assert len(loaded.nodes) == len(simple_tree.nodes)
