# Module 03 — Parallel Execution

> Run multiple agents simultaneously and collect their results.

## What You'll Build

A **product analysis system** with three expert agents (market, technical, customer) that analyze the same product in parallel and produce independent reports.

## Run It

```bash
# Flock version (automatic parallelism)
uv run 03-parallel-execution/flock/parallel.py

# Agent Framework version (explicit fan-out/fan-in)
uv run 03-parallel-execution/agent_framework/parallel.py
```

## How They Achieve Parallelism

### Flock — Automatic

```python
# Three agents consume the same type → all trigger simultaneously
flock.agent("market").consumes(ProductInfo).publishes(MarketAnalysis)
flock.agent("tech").consumes(ProductInfo).publishes(TechnicalReview)
flock.agent("customer").consumes(ProductInfo).publishes(CustomerInsight)

# One publish triggers all three in parallel
await flock.publish(product)
await flock.run_until_idle()
```

No parallelism configuration. It's the *default behavior* when multiple agents subscribe to the same type.

### Agent Framework — Explicit Fan-Out/Fan-In

```python
workflow = (
    WorkflowBuilder(start_executor=dispatcher)
    .add_fan_out_edges(dispatcher, [market, tech, customer])    # parallel
    .add_fan_in_edges([market, tech, customer], aggregator)     # join
    .build()
)
```

You explicitly declare which agents run in parallel and how their results are collected.

## Comparison

| Aspect | Flock | Agent Framework |
|--------|-------|-----------------|
| Parallelism trigger | Automatic (same input type) | Explicit (`add_fan_out_edges`) |
| Synchronization | AND-gate (`.consumes(A, B)`) | `add_fan_in_edges` |
| Adding agent | Just declare it | Add to fan-out AND fan-in arrays |
| Result collection | `store.get_by_type()` | Aggregator receives `list` |
| Visibility | Implicit (must know types) | Explicit (visible in graph) |

## Key Takeaway

- **Flock**: Parallelism is *emergent* — it happens naturally when agents share input types.
- **Agent Framework**: Parallelism is *designed* — you explicitly create the parallel topology.

The trade-off is the same as always: implicit = faster to build, explicit = easier to reason about.

## Next

[Module 04 — Conditional Routing](../04-conditional-routing/) — route data to different agents based on conditions.
