# 🐟 swarm-predict

**A local-first multi-agent prediction engine. Predict anything with swarm intelligence.**

Feed it a scenario, and it builds a society of AI agents that debate, argue, support, and oppose each other over multiple rounds — then generates a prediction report with confidence levels and scenario analysis.

No databases. No vector stores. No heavy ML models. Just LLM API calls and JSON files.

Inspired by [MiroFish](https://github.com/666ghj/MiroFish), but designed to run locally as a CLI tool, inside coding agents (Claude Code, Codex, OpenCode), or as part of an AI assistant workflow (OpenClaw).

## How it works

```
Seed Document → Knowledge Graph → AI Agents → Simulation → Prediction Report
```

1. **Seed** — You provide a markdown document describing the situation (actors, events, context)
2. **Graph** — LLM extracts entities and relationships into a knowledge graph
3. **Enrich** *(optional)* — Gemini with Google Search grounding adds real-time context
4. **Agents** — Each entity becomes an AI agent with objectives, personality, and stance
5. **Simulate** — Agents interact over N rounds: posting opinions, responding, supporting, opposing, changing stances
6. **Report** — LLM analyzes the simulation dynamics and generates a prediction with confidence levels

## Quick start

```bash
# Clone and install
git clone https://github.com/victorianoi/swarm-predict.git
cd swarm-predict
uv sync  # or: pip install -e .

# Set API keys
export OPENAI_API_KEY=sk-...
export GEMINI_API_KEY=AI...  # Optional, for web search enrichment

# Run a prediction
swarm-predict run \
  --seed examples/escribano_indra.md \
  --question "Will Escribano remain as Indra president for 12 more months?" \
  --rounds 10
```

## Installation

### With uv (recommended)

```bash
uv sync
```

### With pip

```bash
pip install -e .
```

### Dependencies

Minimal by design:

- `click` — CLI framework
- `httpx` — Async HTTP client for LLM APIs
- `networkx` — Knowledge graph
- `pydantic` — Data models
- `rich` — Terminal output

No PyTorch, no transformers, no CUDA, no Docker required.

## CLI commands

```bash
# Full pipeline: graph → agents → simulate → report
swarm-predict run --seed scenario.md --question "Will X happen?" --rounds 20

# Build knowledge graph only
swarm-predict graph --seed scenario.md --question "..."

# Regenerate report from existing simulation
swarm-predict report --simulation results/sim_20260326_123456_abc123/

# List agents in a simulation
swarm-predict agents --simulation results/sim_20260326_123456_abc123/

# Interactive chat with a simulated agent (stay in character)
swarm-predict interview --simulation results/sim_20260326_123456_abc123/ --agent "Pedro Sánchez"
```

## Options

| Flag | Default | Description |
|------|---------|-------------|
| `--seed` | *required* | Path to seed document (markdown) |
| `--question` | *required* | The prediction question |
| `--rounds` | `10` | Number of simulation rounds |
| `--reason-model` | `gpt-4o-mini` | Model for reasoning (OpenAI API format) |
| `--search-model` | `gemini-2.0-flash` | Model for web enrichment (Gemini) |
| `--max-agents` | `15` | Maximum number of agents to simulate |
| `--no-enrich` | `false` | Skip web search enrichment |
| `--output` | `results` | Output directory |

## Models

Any OpenAI-compatible API works as the reasoning model. Gemini is optional for web search grounding.

| Role | Default | Purpose | Required |
|------|---------|---------|----------|
| Reasoning | `gpt-4o-mini` | Entity extraction, agent decisions, report generation | Yes |
| Search | `gemini-2.0-flash` | Real-world context enrichment via Google Search | No |

**Cost estimate:** A 10-round simulation with 10 agents uses ~50-80K tokens on `gpt-4o-mini` (~$0.01-0.02). More rounds and agents = more tokens.

## Writing seed documents

The seed document is a markdown file describing the situation you want to predict. Good seeds include:

- **Key actors** — Who are the players? What are their interests?
- **Recent events** — What just happened? What's the timeline?
- **Power dynamics** — Who has leverage? What are the alliances?
- **The question** — What outcome are you trying to predict?

See [`examples/escribano_indra.md`](examples/escribano_indra.md) for a real example (Spanish corporate governance battle).

### Tips

- More context = better agents. Include relationships, motivations, and constraints.
- The `--question` should be a yes/no or outcome-based question.
- Start with 10 rounds to test, then increase to 20-50 for more nuanced results.
- Gemini enrichment adds real-time web context (highly recommended for current events).

## Output structure

Each simulation creates a timestamped directory:

```
results/sim_20260326_123456_abc123/
├── graph.json      # Knowledge graph (entities + relationships)
├── agents.json     # Agent profiles (name, role, stance, objectives)
├── actions.jsonl   # All simulation actions (one per line)
├── report.md       # Final prediction report
└── state.json      # Full simulation state (for resume/re-analysis)
```

## Using with AI coding agents

swarm-predict is designed to work inside AI-assisted workflows. Here's how to use it with different tools:

### OpenClaw / Claude (as a skill or CLI tool)

```bash
# Your AI assistant can run predictions on demand
cd /path/to/swarm-predict
uv run swarm-predict run \
  --seed /tmp/scenario.md \
  --question "Will the merger go through?" \
  --rounds 15
```

The assistant can:
1. Write the seed document from conversation context
2. Run the simulation
3. Read and summarize the report
4. Interview specific agents for deeper analysis

### Claude Code / Codex / OpenCode

Add to your project's `.agents/skills/` or use directly:

```bash
# Install globally
uv tool install /path/to/swarm-predict

# Or run from the repo
cd /path/to/swarm-predict && uv run swarm-predict run --seed ...
```

### Programmatic usage (Python)

```python
import asyncio
from swarm_predict.graph_builder import build_graph
from swarm_predict.agent_generator import generate_agents
from swarm_predict.simulator import run_simulation
from swarm_predict.reporter import generate_report
from swarm_predict.llm.openai_llm import OpenAIProvider

async def predict(seed_text, question):
    llm = OpenAIProvider(api_key="sk-...", model="gpt-4o-mini")

    # Build graph
    graph = await build_graph(seed_text, question, llm)

    # Generate agents
    agents = await generate_agents(graph, question, llm, max_agents=10)

    # Simulate
    actions = await run_simulation(agents, question, rounds=10, llm=llm, output_dir="./out")

    # Report
    report = await generate_report(question, agents, actions, 10, llm)

    await llm.close()
    return report

result = asyncio.run(predict(open("scenario.md").read(), "Will X happen?"))
print(result)
```

## Example: Escribano vs. Spanish Government

The included example simulates the battle over Indra's presidency (March 2026):

```bash
swarm-predict run \
  --seed examples/escribano_indra.md \
  --question "Will Escribano remain as Indra president for 12 more months?" \
  --rounds 10

# Interview the Spanish PM agent
swarm-predict interview \
  --simulation results/sim_*/  \
  --agent "Pedro Sánchez"
```

The simulation creates agents for Escribano, SEPI, Sánchez, T. Rowe Price, independent board members, etc. — each with their own objectives and stance — and lets them interact to see how the situation might evolve.

## Architecture

```
swarm_predict/
├── cli.py              # CLI entry point (Click)
├── config.py           # Configuration and env vars
├── models.py           # Pydantic data models
├── graph_builder.py    # Entity/relationship extraction → knowledge graph
├── enricher.py         # Optional Gemini web search grounding
├── agent_generator.py  # Create agent profiles from graph entities
├── simulator.py        # Multi-round agent interaction engine
├── reporter.py         # Prediction report generation
├── interviewer.py      # Interactive agent chat
└── llm/
    ├── base.py         # Abstract LLM provider
    ├── openai_llm.py   # OpenAI-compatible provider (async, batch)
    ├── gemini_llm.py   # Gemini provider with Google Search grounding
    └── utils.py        # JSON extraction from LLM responses
```

**Design principles:**

- **No external services** — No databases, no vector stores, no Zep, no Redis. Everything is files.
- **Async parallel** — Agent decisions run concurrently via asyncio (10x semaphore)
- **Pluggable models** — Any OpenAI-compatible API works. Swap models freely.
- **File-based state** — All results in JSON/JSONL. Easy to inspect, version, and share.
- **Minimal dependencies** — 5 Python packages. Installs in seconds.

## Limitations

- Agent reasoning quality depends heavily on the LLM model used
- Short simulations (<10 rounds) may not capture complex dynamics
- No persistent memory between simulations (agents start fresh each run)
- Web enrichment requires Gemini API key (free tier works fine)
- Seed document quality directly affects prediction quality

## License

MIT

## Credits

Inspired by [MiroFish](https://github.com/666ghj/MiroFish) — a more full-featured multi-agent prediction platform with UI, persistent memory (Zep), and Docker deployment.

Other related projects:
- [DeepMimic](https://deepmimic.ai/) — Synthetic market research with AI personas
- [Artificial Societies](https://societies.io/) — Stakeholder opinion simulation
