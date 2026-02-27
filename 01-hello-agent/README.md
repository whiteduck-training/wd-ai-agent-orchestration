# Module 01 — Hello Agent

> Build your first AI agent in both frameworks and see two architectures in action.

## What You'll Build

A **poem generator** — the simplest possible agent that takes a topic and produces a poem. Same task, two very different implementations.

## Run It

```bash
# Flock version (blackboard)
uv run 01-hello-agent/flock/hello_agent.py

# Agent Framework version (DAG)
uv run 01-hello-agent/agent_framework/hello_agent.py
```

## Side-by-Side Comparison

### Defining the Agent's "Contract"

**Flock** — explicit types define what goes in and what comes out:

```python
@flock_type
class PoemRequest(BaseModel):
    topic: str
    style: str = "free verse"

@flock_type
class Poem(BaseModel):
    title: str
    text: str
    style: str

poet = flock.agent("poet").consumes(PoemRequest).publishes(Poem)
```

**Agent Framework** — instructions define behavior in natural language:

```python
poet = client.as_agent(
    name="poet",
    instructions="You are a creative poet. When given a topic and style, write a poem..."
)
```

| Aspect | Flock | Agent Framework |
|--------|-------|-----------------|
| Contract | Pydantic types (compile-time) | Instruction strings (runtime) |
| Validation | Automatic via Pydantic | Manual parsing needed |
| Flexibility | Structured, predictable | Freeform, adaptable |
| Discoverability | Types document the API | Instructions describe behavior |

### Running the Agent

**Flock** — publish to blackboard, agent triggers automatically:

```python
await flock.publish(PoemRequest(topic="AI", style="haiku"))
await flock.run_until_idle()
poems = await flock.store.get_by_type(Poem)
```

**Agent Framework** — call the agent directly:

```python
result = await poet_agent.run("Write a haiku about AI")
print(result)
```

| Aspect | Flock | Agent Framework |
|--------|-------|-----------------|
| Trigger | Automatic (data appears) | Explicit (you call it) |
| Input | Typed artifact object | String message |
| Output | Typed artifact on blackboard | Response object |
| Multiple runs | Publish multiple artifacts | Call run() multiple times |

## Key Takeaway

Both frameworks accomplish the same task, but they think about it differently:

- **Flock** says: "Define your data types. Agents are subscriptions to those types."
- **Agent Framework** says: "Define your agent's behavior. Call it when you need it."

Neither is better — they optimize for different things. As the workshop progresses, you'll see where each approach shines.

## Next

[Module 02 — Multi-Agent](../02-multi-agent/) — chain multiple agents together into a pipeline.
