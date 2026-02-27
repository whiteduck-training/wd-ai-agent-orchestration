# Module 02 — Multi-Agent Pipeline

> Chain multiple agents into a sequential content creation pipeline.

## What You'll Build

A **content pipeline**: Topic → Outline → Draft. Two agents work in sequence — the outliner produces structure, the writer produces prose.

## Run It

```bash
# Flock version (type cascade)
uv run 02-multi-agent/flock/pipeline.py

# Agent Framework version (explicit graph)
uv run 02-multi-agent/agent_framework/pipeline.py
```

## How They Wire the Pipeline

### Flock — Type Cascade (Implicit)

```python
outliner: TopicRequest → ContentOutline
writer:   ContentOutline → ContentDraft
```

No explicit connections. The outliner publishes a `ContentOutline`; the writer consumes `ContentOutline`. The pipeline *emerges* from type dependencies.

### Agent Framework — Graph Edges (Explicit)

```python
workflow = (
    WorkflowBuilder(start_executor=outliner_agent)
    .add_edge(outliner_agent, writer_agent)
    .build()
)
```

You explicitly wire the outliner's output to the writer's input. The graph is visible and deterministic.

## Comparison

| Aspect | Flock | Agent Framework |
|--------|-------|-----------------|
| Wiring | Implicit (type matching) | Explicit (`.add_edge()`) |
| Adding a stage | Add agent + types | Add agent + wire edges |
| Intermediate data | On blackboard (inspectable) | Passed along edges |
| Debugging | Check blackboard artifacts | Trace graph execution |
| Extensibility | New agent "just works" | New agent needs new edges |

## Key Takeaway

- **Flock** pipelines are *discovered* — the orchestrator figures out the execution order from type dependencies.
- **Agent Framework** pipelines are *declared* — you draw the graph explicitly.

Both work. The trade-off: implicit wiring is faster to extend but harder to reason about; explicit wiring is more verbose but completely transparent.

## Next

[Module 03 — Parallel Execution](../03-parallel-execution/) — run multiple agents simultaneously on the same input.
