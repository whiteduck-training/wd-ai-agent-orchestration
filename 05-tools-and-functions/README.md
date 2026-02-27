# Module 05 — Tools & Functions

> Give agents the ability to call external functions for real-world data.

## What You'll Build

A **travel planner** that uses tools to check weather, convert currency, and find attractions — then creates a trip plan using real (simulated) data.

## Run It

```bash
# Flock version (litellm tools)
uv run 05-tools-and-functions/flock/tools.py

# Agent Framework version (@tool decorator)
uv run 05-tools-and-functions/agent_framework/tools.py
```

## How They Define Tools

### Flock — Function Passing

```python
def get_weather(city: str) -> str:
    """Get weather for a city."""
    return f"{city}: sunny, 25°C"

agent = (
    flock.agent("planner")
    .consumes(TravelRequest)
    .publishes(TravelPlan)
    .tools(get_weather, convert_currency)
)
```

Tools are regular Python functions passed via `.tools()`. Flock uses litellm's function calling protocol.

### Agent Framework — @tool Decorator

```python
@tool(approval_mode="never_require")
def get_weather(
    city: Annotated[str, Field(description="The city to check")],
) -> str:
    """Get weather for a city."""
    return f"{city}: sunny, 25°C"

agent = client.as_agent(
    name="planner",
    tools=[get_weather, convert_currency],
)
```

Tools use the `@tool` decorator with explicit parameter descriptions and approval control.

## Comparison

| Aspect | Flock | Agent Framework |
|--------|-------|-----------------|
| Tool definition | Regular functions | `@tool` decorator |
| Parameter docs | Docstrings | `Annotated[type, Field()]` |
| Approval control | Not available | `approval_mode` per tool |
| Passing to agent | `.tools(fn1, fn2)` | `tools=[fn1, fn2]` |
| Protocol | litellm function calling | OpenAI function calling |

## Key Takeaway

Both frameworks let agents call tools, but with different levels of control:

- **Flock** keeps it simple — pass functions, the agent calls them.
- **Agent Framework** adds governance — approval modes, structured parameter descriptions, and tool-level configuration.

For workshops and prototypes, simplicity wins. For production systems, the extra control matters.

## Next

[Module 06 — Architecture Deep Dive](../06-architecture-deep-dive/) — no code, all theory. Understand the internals.
