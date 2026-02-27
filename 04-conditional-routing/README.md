# Module 04 — Conditional Routing

> Route data to different agents based on runtime conditions.

## What You'll Build

A **support ticket router** that classifies incoming tickets and routes them to the appropriate handler (senior, experienced, or standard support) based on priority and customer tier.

## Run It

```bash
# Flock version (where= predicates)
uv run 04-conditional-routing/flock/conditional.py

# Agent Framework version (switch-case edges)
uv run 04-conditional-routing/agent_framework/conditional.py
```

## How They Route

### Flock — Decentralized (where= Predicates)

```python
# Each agent declares its own filter
senior = flock.agent("senior").consumes(
    Ticket, where=lambda t: t.priority == "critical"
)
standard = flock.agent("standard").consumes(
    Ticket, where=lambda t: t.priority in ("normal", "low")
)
```

Routing is distributed across agent declarations. Each agent decides what it handles.

### Agent Framework — Centralized (Switch-Case)

```python
workflow = (
    WorkflowBuilder(start_executor=intake)
    .add_edge(intake, classifier)
    .add_switch_case_edge_group(classifier, [
        Case(condition=is_critical, target=senior_handler),
        Case(condition=is_high, target=experienced_handler),
        Default(target=standard_handler),
    ])
    .build()
)
```

Routing is centralized in one switch-case decision point.

## Comparison

| Aspect | Flock | Agent Framework |
|--------|-------|-----------------|
| Routing style | Decentralized (per-agent) | Centralized (switch-case) |
| Adding a route | Add agent with `where=` | Add `Case` to switch group |
| Overlapping routes | Multiple agents can match | First matching Case wins |
| Visibility | Spread across agents | All routes visible in one place |
| Testing routes | Test each agent's predicate | Test each Case condition |

## Key Takeaway

- **Flock** distributes routing decisions to the agents themselves — each agent is responsible for filtering its own input.
- **Agent Framework** centralizes routing in the graph — one switch-case controls all paths.

Decentralized routing scales better when routes change independently; centralized routing is easier to audit and debug.

## Next

[Module 05 — Tools & Functions](../05-tools-and-functions/) — give agents the ability to call external functions.
