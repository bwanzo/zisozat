"""Tests for the CLI commands (no real AI calls)."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from zisozat.cli import main
from zisozat.models import DecisionTree

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_VALID_TREE_JSON = json.dumps(
    {
        "title": "Test tree",
        "description": "CLI test",
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


def _make_tree() -> DecisionTree:
    return DecisionTree.from_json(_VALID_TREE_JSON)


# ---------------------------------------------------------------------------
# generate command
# ---------------------------------------------------------------------------


class TestGenerateCommand:
    def test_generate_saves_file(self, tmp_path):
        output = tmp_path / "tree.json"
        runner = CliRunner()

        with patch("zisozat.cli.get_generator") as mock_get:
            mock_gen = MagicMock()
            mock_gen.generate.return_value = _make_tree()
            mock_get.return_value = mock_gen

            result = runner.invoke(
                main,
                ["generate", "Should I adopt a dog?", "--provider", "claude",
                 "--output", str(output), "--no-run"],
            )

        assert result.exit_code == 0, result.output
        assert output.exists()
        loaded = DecisionTree.load(output)
        assert loaded.title == "Test tree"

    def test_generate_runs_interactive(self, tmp_path):
        runner = CliRunner()

        with patch("zisozat.cli.get_generator") as mock_get:
            mock_gen = MagicMock()
            mock_gen.generate.return_value = _make_tree()
            mock_get.return_value = mock_gen

            # Simulate user entering "1" (Yes → "Go outside!") then quitting
            result = runner.invoke(
                main,
                ["generate", "weather", "--provider", "claude", "--run"],
                input="1\n",
            )

        assert result.exit_code == 0, result.output
        assert "Go outside!" in result.output

    def test_generate_bad_provider_import_error(self):
        runner = CliRunner()

        with patch("zisozat.cli.get_generator", side_effect=ImportError("missing package")):
            result = runner.invoke(main, ["generate", "topic", "--provider", "claude", "--no-run"])

        assert result.exit_code != 0

    def test_generate_api_error(self):
        runner = CliRunner()

        with patch("zisozat.cli.get_generator") as mock_get:
            mock_gen = MagicMock()
            mock_gen.generate.side_effect = RuntimeError("API timeout")
            mock_get.return_value = mock_gen

            result = runner.invoke(main, ["generate", "topic", "--provider", "openai", "--no-run"])

        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# run command
# ---------------------------------------------------------------------------


class TestRunCommand:
    def test_run_loads_and_walks(self, tmp_path):
        path = tmp_path / "tree.json"
        _make_tree().save(path)
        runner = CliRunner()
        result = runner.invoke(main, ["run", str(path)], input="2\n")
        assert result.exit_code == 0, result.output
        assert "Stay inside." in result.output

    def test_run_missing_file(self):
        runner = CliRunner()
        result = runner.invoke(main, ["run", "/nonexistent/tree.json"])
        assert result.exit_code != 0

    def test_run_quit_mid_session(self, tmp_path):
        path = tmp_path / "tree.json"
        _make_tree().save(path)
        runner = CliRunner()
        result = runner.invoke(main, ["run", str(path)], input="q\n")
        assert result.exit_code == 0, result.output
        assert "ended" in result.output.lower()


# ---------------------------------------------------------------------------
# visualize command
# ---------------------------------------------------------------------------


class TestVisualizeCommand:
    def test_visualize_prints_tree(self, tmp_path):
        path = tmp_path / "tree.json"
        _make_tree().save(path)
        runner = CliRunner()
        result = runner.invoke(main, ["visualize", str(path)])
        assert result.exit_code == 0, result.output
        # Should contain the question and at least one option
        assert "sunny" in result.output.lower() or "yes" in result.output.lower()

    def test_visualize_missing_file(self):
        runner = CliRunner()
        result = runner.invoke(main, ["visualize", "/nonexistent/tree.json"])
        assert result.exit_code != 0
