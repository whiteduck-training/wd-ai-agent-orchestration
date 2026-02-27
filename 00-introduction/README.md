# Module 00 — Introduction

> Before writing code, let's build the mental models you need to understand multi-agent AI systems.

## What Are Agent Orchestration Frameworks?

When you move beyond a single LLM call, you need **orchestration** — a way to coordinate multiple AI agents working together. Agent orchestration frameworks provide:

- **Agent lifecycle management** — creating, configuring, and running agents
- **Communication patterns** — how agents exchange data
- **Execution control** — sequencing, parallelism, and conditional routing
- **State management** — tracking context across agent interactions

## Two Approaches, Two Philosophies

This workshop compares two fundamentally different architectures:

### Blackboard Architecture (Flock)

Think of a **shared whiteboard** in a meeting room. Specialists walk up, read what's relevant to them, do their work, and post results back. Nobody tells them when to act — they just watch for their kind of data.

- Agents **react to typed data** appearing on the blackboard
- No agent knows about any other agent
- Parallelism happens **automatically**
- Adding new capabilities = adding new agents (zero changes to existing ones)

### DAG Architecture (Microsoft Agent Framework)

Think of an **assembly line** in a factory. Each station knows exactly where parts come from and where they go next. The blueprint shows the entire flow before anything runs.

- Agents are **connected by explicit edges** in a graph
- You can see the **entire execution path** upfront
- Parallelism is **explicitly designed** with fan-out/fan-in
- Adding new capabilities = adding nodes and wiring edges

## Vocabulary Mapping

The same concepts have different names in each framework:

| Concept | Flock Term | Agent Framework Term |
|---------|-----------|---------------------|
| The orchestrator | `Flock()` | `WorkflowBuilder` |
| An AI worker | Agent | Agent / Executor |
| Input specification | `.consumes(Type)` | Handler input type |
| Output specification | `.publishes(Type)` | `ctx.send_message()` / `ctx.yield_output()` |
| Data container | Artifact (Pydantic model) | Message |
| Sequential flow | Type cascade (A→B→C) | `.add_edge(a, b)` |
| Parallel branches | Auto (same input type) | `.add_fan_out_edges()` |
| Wait for all | AND-gate (`.consumes(A, B)`) | `.add_fan_in_edges()` |
| Conditional routing | `where=` predicate | `.add_switch_case_edge_group()` |
| Shared state | Blackboard (`flock.store`) | `WorkflowContext` state dict |
| Run everything | `flock.run_until_idle()` | `workflow.run()` |
| Get results | `flock.store.get_by_type()` | `events.get_outputs()` |

## Setup Checklist

Before starting Module 01, make sure you have:

- [ ] **GitHub Codespace running** (or local environment with Python 3.12+ and uv)
- [ ] **Dependencies installed**: `uv sync`
- [ ] **Environment configured**: `.env` file with your `OPENAI_API_KEY`
- [ ] **Smoke test passing**:

```bash
uv run 00-introduction/smoke_test.py
```

This verifies Python version, imports, API key, and makes one test call through each framework. You should see all `[PASS]` before moving on.

## What's Next

In **[Module 01 — Hello Agent](../01-hello-agent/)**, you'll build your first agent in both frameworks and see the architectural differences in action.
