# zisozat

**AI-powered decision tree tool** – generate interactive decision trees on any topic using Claude or OpenAI, then walk through them step-by-step in your terminal.

---

## Features

- 🤖 **Multi-provider AI** – Claude (Anthropic) and OpenAI out of the box; easily extensible
- 🌳 **Interactive CLI** – guided question-and-answer sessions with Rich formatting
- 💾 **Save & load** – export trees to JSON, reload and rerun at any time
- 🗺️ **Visualise** – print a tree diagram of any saved decision tree
- 🧩 **Python API** – use the models and runner directly in your own code

---

## Installation

```bash
pip install zisozat
```

> **Tip:** Install only the AI provider you need:
> ```bash
> pip install anthropic   # for Claude
> pip install openai      # for OpenAI
> ```

---

## Quick start

### Generate and run a tree interactively

```bash
# Using Claude (default)
export ANTHROPIC_API_KEY="sk-ant-..."
zisozat generate "Should I adopt a dog?"

# Using OpenAI
export OPENAI_API_KEY="sk-..."
zisozat generate "Choosing a cloud database" --provider openai

# Save the tree to a file and run it later
zisozat generate "Career change decision" --output career.json --no-run
zisozat run career.json
```

### Visualise a saved tree

```bash
zisozat visualize career.json
```

---

## CLI reference

```
Usage: zisozat [OPTIONS] COMMAND [ARGS]...

  zisozat – AI-powered decision tree tool.

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  generate   Generate a decision tree for TOPIC using an AI provider.
  run        Walk through a previously saved decision tree interactively.
  visualize  Print a tree diagram of a saved decision tree.
```

### `generate` options

| Flag | Default | Description |
|------|---------|-------------|
| `--provider`, `-p` | `claude` | AI provider (`claude` or `openai`) |
| `--model`, `-m` | provider default | Model name (e.g. `claude-opus-4-5`, `gpt-4o`) |
| `--api-key`, `-k` | env var | API key (falls back to `ANTHROPIC_API_KEY` / `OPENAI_API_KEY`) |
| `--output`, `-o` | — | Save the generated tree as a JSON file |
| `--run/--no-run` | `--run` | Start an interactive session immediately after generation |

---

## Python API

```python
from zisozat.generators import get_generator
from zisozat.models import DecisionTree
from zisozat.tree import TreeRunner

# Generate
generator = get_generator("claude", api_key="sk-ant-...")
tree: DecisionTree = generator.generate("Should I learn Rust?")

# Save / load
tree.save("rust.json")
tree = DecisionTree.load("rust.json")

# Traverse programmatically
runner = TreeRunner(tree)
while not runner.is_done:
    node = runner.current_node
    print(node.question)
    print(node.options)
    runner.choose(node.options[0])   # always pick the first option

print(runner.current_node.conclusion)
```

---

## Adding a new provider

1. Create `src/zisozat/generators/myprovider.py` subclassing `BaseGenerator`.
2. Implement `_call_api(self, topic: str) -> str` (return the raw JSON string from the model).
3. Register it in `src/zisozat/generators/__init__.py`'s `mapping` dict.

---

## Development

```bash
git clone https://github.com/bwanzo/zisozat.git
cd zisozat
pip install -e ".[dev]"
pytest
```

---

## License

MIT
