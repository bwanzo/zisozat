"""Command-line interface for zisozat."""

from __future__ import annotations

import os
import sys
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text
from rich.tree import Tree as RichTree

from zisozat.generators import get_generator
from zisozat.models import DecisionTree
from zisozat.tree import TreeRunner

console = Console()


# ---------------------------------------------------------------------------
# CLI group
# ---------------------------------------------------------------------------


@click.group()
@click.version_option(package_name="zisozat")
def main() -> None:
    """zisozat – AI-powered decision tree tool.

    Use Claude, OpenAI or another provider to generate interactive
    decision trees on any topic, then walk through them in the terminal.
    """


# ---------------------------------------------------------------------------
# generate
# ---------------------------------------------------------------------------


@main.command()
@click.argument("topic")
@click.option(
    "--provider",
    "-p",
    default="claude",
    show_default=True,
    type=click.Choice(["claude", "openai"], case_sensitive=False),
    help="AI provider to use.",
)
@click.option(
    "--model",
    "-m",
    default=None,
    help="Model name (provider-specific default used if omitted).",
)
@click.option(
    "--api-key",
    "-k",
    default=None,
    envvar=["ANTHROPIC_API_KEY", "OPENAI_API_KEY"],
    help="API key (falls back to ANTHROPIC_API_KEY / OPENAI_API_KEY env vars).",
)
@click.option(
    "--output",
    "-o",
    default=None,
    type=click.Path(dir_okay=False, writable=True),
    help="Save the generated tree as a JSON file.",
)
@click.option(
    "--run/--no-run",
    default=True,
    show_default=True,
    help="Start an interactive session after generating.",
)
def generate(
    topic: str,
    provider: str,
    model: Optional[str],
    api_key: Optional[str],
    output: Optional[str],
    run: bool,
) -> None:
    """Generate a decision tree for TOPIC using an AI provider.

    TOPIC can be any question or subject, e.g.
    "Should I adopt a dog?" or "Choosing a cloud database".
    """
    # Resolve API key from common env-var names when not provided explicitly
    if api_key is None:
        env_map = {"claude": "ANTHROPIC_API_KEY", "openai": "OPENAI_API_KEY"}
        api_key = os.environ.get(env_map.get(provider.lower(), ""))

    generator_kwargs: dict = {"api_key": api_key}
    if model:
        generator_kwargs["model"] = model

    console.print(
        f"\n[bold cyan]Generating decision tree for:[/bold cyan] [italic]{topic}[/italic]"
        f" [dim](provider: {provider})[/dim]\n"
    )

    try:
        generator = get_generator(provider, **generator_kwargs)
    except ImportError as exc:
        console.print(f"[red]Import error:[/red] {exc}")
        sys.exit(1)

    with console.status("[cyan]Calling AI…[/cyan]"):
        try:
            tree = generator.generate(topic)
        except Exception as exc:  # noqa: BLE001
            console.print(f"[red]Generation failed:[/red] {exc}")
            sys.exit(1)

    console.print(f"[green]✓[/green] Tree '{tree.title}' generated with {len(tree.nodes)} nodes.")

    if output:
        tree.save(output)
        console.print(f"[green]✓[/green] Saved to [bold]{output}[/bold]")

    if run:
        _run_interactive(tree)


# ---------------------------------------------------------------------------
# run
# ---------------------------------------------------------------------------


@main.command("run")
@click.argument("file", type=click.Path(exists=True, dir_okay=False))
def run_cmd(file: str) -> None:
    """Walk through a previously saved decision tree interactively.

    FILE must be a JSON file produced by the ``generate`` command.
    """
    try:
        tree = DecisionTree.load(file)
    except Exception as exc:  # noqa: BLE001
        console.print(f"[red]Failed to load tree:[/red] {exc}")
        sys.exit(1)

    _run_interactive(tree)


# ---------------------------------------------------------------------------
# visualise
# ---------------------------------------------------------------------------


@main.command("visualize")
@click.argument("file", type=click.Path(exists=True, dir_okay=False))
def visualize_cmd(file: str) -> None:
    """Print a tree diagram of a saved decision tree.

    FILE must be a JSON file produced by the ``generate`` command.
    """
    try:
        tree = DecisionTree.load(file)
    except Exception as exc:  # noqa: BLE001
        console.print(f"[red]Failed to load tree:[/red] {exc}")
        sys.exit(1)

    _print_tree(tree)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _run_interactive(tree: DecisionTree) -> None:
    """Drive an interactive CLI session for *tree*."""
    runner = TreeRunner(tree)

    console.print()
    console.print(
        Panel.fit(
            f"[bold]{tree.title}[/bold]\n{tree.description}",
            title="Decision Tree",
        )
    )
    console.print()

    while not runner.is_done:
        node = runner.current_node
        console.print(f"[bold yellow]❓ {node.question}[/bold yellow]")

        for i, option in enumerate(node.options, 1):
            console.print(f"  [cyan]{i}.[/cyan] {option}")

        console.print()
        while True:
            raw = Prompt.ask(
                f"[dim]Enter 1–{len(node.options)} (or 'q' to quit)[/dim]",
                console=console,
            )
            if raw.lower() == "q":
                console.print("\n[dim]Session ended.[/dim]")
                return
            try:
                idx = int(raw)
                if 1 <= idx <= len(node.options):
                    chosen = node.options[idx - 1]
                    break
                console.print(
                    f"[red]Please enter a number between 1 and {len(node.options)}.[/red]"
                )
            except ValueError:
                console.print("[red]Please enter a valid number or 'q'.[/red]")

        runner.choose(chosen)
        console.print()

    conclusion_node = runner.current_node
    console.print(
        Panel.fit(
            f"[bold green]{conclusion_node.conclusion}[/bold green]",
            title="[bold]Conclusion[/bold]",
        )
    )
    console.print()


def _print_tree(
    tree: DecisionTree,
    node_id: str | None = None,
    rich_node: RichTree | None = None,
) -> None:
    """Recursively print *tree* using Rich's tree widget."""
    if node_id is None:
        # Root call
        node = tree.root
        root_label = Text(f"[{node.id}] {node.question or node.conclusion or '(root)'}")
        rich_root = RichTree(root_label)
        _print_tree(tree, node_id=node.id, rich_node=rich_root)
        console.print(rich_root)
        return

    node = tree.nodes[node_id]
    for option, child_id in node.children.items():
        child = tree.nodes.get(child_id)
        if child is None:
            continue
        if child.conclusion:
            label = Text(f"[{option}] → [green]{child.conclusion}[/green]")
        else:
            label = Text(f"[{option}] → [{child.id}] {child.question}")
        child_rich = rich_node.add(label)  # type: ignore[union-attr]
        _print_tree(tree, node_id=child_id, rich_node=child_rich)
