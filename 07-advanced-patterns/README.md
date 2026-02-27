# Module 07 — Advanced Patterns

> Complex orchestration patterns: fan-out/join and feedback loops.

## What You'll Build

Two advanced patterns that appear in real-world agent systems:

1. **Fan-Out + Join** — One input triggers parallel processing, results are aggregated
2. **Feedback Loop** — Iterative refinement until quality threshold is met

## Run It

```bash
# Fan-Out + Join
uv run 07-advanced-patterns/flock/fan_out_join.py
uv run 07-advanced-patterns/agent_framework/fan_out_join.py

# Feedback Loop
uv run 07-advanced-patterns/flock/feedback_loop.py
uv run 07-advanced-patterns/agent_framework/loop.py
```

## Pattern 1: Fan-Out + Join

### Flock — Type-Based AND-Gate

```python
# Fan-out: three agents consume the same type (automatic)
security.consumes(CodeSubmission).publishes(SecurityReview)
performance.consumes(CodeSubmission).publishes(PerformanceReview)
style.consumes(CodeSubmission).publishes(StyleReview)

# AND-gate: waits for ALL review types
merger.consumes(SecurityReview, PerformanceReview, StyleReview)
```

### Agent Framework — Explicit Graph Edges

```python
workflow = (
    WorkflowBuilder(start_executor=dispatcher)
    .add_fan_out_edges(dispatcher, [security, performance, style])
    .add_fan_in_edges([security, performance, style], merger)
    .build()
)
```

| Aspect | Flock | Agent Framework |
|--------|-------|-----------------|
| Fan-out | Automatic (same input type) | `add_fan_out_edges()` |
| Join/barrier | `.consumes(A, B, C)` AND-gate | `add_fan_in_edges()` barrier |
| Adding branch | Add agent (zero changes) | Update fan-out AND fan-in arrays |
| Aggregation | Merger sees typed artifacts | Merger receives `list` of responses |

## Pattern 2: Feedback Loop

### Flock — Self-Consuming Agent

```python
# Agent consumes and publishes the SAME type
refiner = (
    flock.agent("refiner")
    .consumes(EssayDraft, where=lambda d: d.quality_score < 7)
    .publishes(EssayDraft)  # same type → creates a loop
)
# Loop stops when where= no longer matches
```

### Agent Framework — Graph Cycle with State

```python
workflow = (
    WorkflowBuilder(start_executor=seed)
    .add_edge(seed, writer)
    .add_edge(writer, evaluate)
    .add_switch_case_edge_group(evaluate, [
        Case(condition=needs_refinement, target=refine_prompt),
        Default(target=finalize),
    ])
    .add_edge(refine_prompt, writer)  # LOOP BACK
    .build()
)
```

| Aspect | Flock | Agent Framework |
|--------|-------|-----------------|
| Loop mechanism | Self-consuming type | Graph cycle edge |
| Break condition | `where=` predicate | Switch-case condition |
| State tracking | Artifact fields (iteration, score) | `ctx.set_state()` / `get_state()` |
| Visibility | Implicit (type produces itself) | Explicit (visible cycle in graph) |

## Key Takeaway

Advanced patterns amplify the architectural differences:

- **Flock** achieves complexity through **type relationships** — AND-gates, self-consumption, and predicates create powerful patterns with minimal code.
- **Agent Framework** achieves complexity through **graph topology** — explicit fan-out/in, cycles, and state management make every step visible.

## Next

[Module 08 — When to Use Which](../08-when-to-use-which/) — a decision framework for choosing the right approach.
