# AI Agent Orchestration Workshop

> **Compare two fundamentally different approaches to multi-agent AI systems — side by side.**

This workshop teaches you to build AI agent systems using two frameworks that represent different architectural philosophies:

| | **Flock** | **Microsoft Agent Framework** |
|---|---|---|
| **Architecture** | Event-driven blackboard | DAG / superstep graph |
| **Coupling** | Loose — agents react to typed artifacts | Explicit — agents connected by edges |
| **Parallelism** | Automatic — multiple agents triggered simultaneously | Explicit — fan-out edges define parallel branches |
| **Best for** | Exploratory, evolving systems | Deterministic, auditable pipelines |

## Quick Start (GitHub Codespace)

1. Click the button below to launch a preconfigured environment:

   [![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/whiteduck-training/wd-ai-agent-orchestration)

2. Copy the environment template and configure credentials:
   ```bash
   cp .env_template .env
   # Edit .env for either:
   # - OpenAI mode (OPENAI_API_KEY), or
   # - Azure mode (AZURE_API_KEY, AZURE_API_BASE, DEFAULT_MODEL=azure/<deployment>)
   ```

3. Run your first example:
   ```bash
   # Flock version
   uv run 01-hello-agent/flock/hello_agent.py

   # Agent Framework version
   uv run 01-hello-agent/agent_framework/hello_agent.py
   ```

## Local Setup

```bash
# Clone the repository
git clone https://github.com/whiteduck-training/wd-ai-agent-orchestration.git
cd wd-ai-agent-orchestration

# Install dependencies (requires uv: https://docs.astral.sh/uv/)
uv sync

# Configure environment
cp .env_template .env
# Edit .env for OpenAI or Azure mode
```

## Workshop Modules

| Module | Topic | What You Build |
|--------|-------|----------------|
| [00 — Introduction](./00-introduction/) | Theory & setup | Vocabulary, mental models |
| [01 — Hello Agent](./01-hello-agent/) | Your first agent | Poem generator in both frameworks |
| [02 — Multi-Agent](./02-multi-agent/) | Sequential pipelines | Content creation pipeline |
| [03 — Parallel Execution](./03-parallel-execution/) | Concurrent agents | Product analysis with 3 parallel experts |
| [04 — Conditional Routing](./04-conditional-routing/) | Dynamic paths | Support ticket router |
| [05 — Tools & Functions](./05-tools-and-functions/) | External capabilities | Travel planner with weather + currency tools |
| [06 — Architecture Deep Dive](./06-architecture-deep-dive/) | Theory (no code) | Blackboard internals vs superstep mechanics |
| [07 — Advanced Patterns](./07-advanced-patterns/) | Fan-out/join, loops | Complex orchestration patterns |
| [08 — When to Use Which](./08-when-to-use-which/) | Decision framework | Choosing the right framework for your use case |

## Running Examples

Every example follows the same pattern:

```bash
# Run the Flock version
uv run <module>/flock/<script>.py

# Run the Agent Framework version
uv run <module>/agent_framework/<script>.py
```

## Environment Variables

| Variable | Used By | Purpose |
|----------|---------|---------|
| `DEFAULT_MODEL` | Both | Provider/model selector (`openai/gpt-4.1` or `azure/<deployment>`) |
| `OPENAI_API_KEY` | Flock + Agent Framework (OpenAI mode) | OpenAI API key |
| `OPENAI_RESPONSES_MODEL_ID` | Agent Framework (OpenAI mode) | Responses model ID (default: `gpt-4.1`) |
| `AZURE_API_KEY` | Flock + Agent Framework (Azure mode) | Azure API key |
| `AZURE_API_BASE` | Flock + Agent Framework (Azure mode) | Azure endpoint URL |
| `AZURE_API_VERSION` | Flock + Agent Framework (Azure mode) | Azure API version (optional) |

Agent Framework auto-selects provider:
- Uses Azure when `AZURE_API_KEY` + `AZURE_API_BASE` are set and `DEFAULT_MODEL=azure/<deployment>`.
- Otherwise falls back to OpenAI settings.

## Quick Reference

Keep the **[CHEATSHEET.md](./CHEATSHEET.md)** open while coding — it has both APIs side by side with zero prose.

## Prerequisites

- Python 3.12+
- Either:
  - An OpenAI API key with access to GPT-4.1, or
  - Azure Foundry/Azure OpenAI credentials (`AZURE_API_KEY`, `AZURE_API_BASE`) and a deployment name in `DEFAULT_MODEL=azure/<deployment>`
- [uv](https://docs.astral.sh/uv/) package manager

## License

MIT — see [LICENSE](./LICENSE)
