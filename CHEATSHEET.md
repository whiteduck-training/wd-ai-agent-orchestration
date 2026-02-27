# Cheat Sheet — Flock vs Agent Framework

> Keep this open while coding. No prose, just patterns.

## Setup

```python
# Flock                                  # Agent Framework
from flock import Flock                  from agent_framework.openai import OpenAIResponsesClient
                                         from agent_framework.azure import AzureOpenAIResponsesClient
from flock.registry import flock_type    from agent_framework import WorkflowBuilder
from pydantic import BaseModel, Field    from agent_framework import Executor, handler, executor
                                         from agent_framework import Case, Default
flock = Flock()                          # OpenAI mode:
                                         client = OpenAIResponsesClient()
                                         # Azure mode:
                                         client = AzureOpenAIResponsesClient(
                                             api_key="...",
                                             endpoint="https://...cognitiveservices.azure.com/",
                                             deployment_name="...",
                                         )
```

## Single Agent

```python
# ── Flock ──────────────────────────    # ── Agent Framework ────────────────
@flock_type                              agent = client.as_agent(
class Request(BaseModel):                    name="poet",
    topic: str                               instructions="Write a poem.",
                                         )
@flock_type
class Response(BaseModel):               # Run
    text: str                            result = await agent.run("about AI")
                                         print(result)
agent = (
    flock.agent("poet")                  # Streaming
    .description("Write a poem.")        async for chunk in agent.run("about AI", stream=True):
    .consumes(Request)                       if chunk.text:
    .publishes(Response)                         print(chunk.text, end="")
)

# Run
await flock.publish(Request(topic="AI"))
await flock.run_until_idle()
results = await flock.store.get_by_type(Response)
```

## Sequential Pipeline

```python
# ── Flock (type cascade) ──────────    # ── Agent Framework (edges) ────────
# Types create the pipeline:             writer = client.as_agent(name="writer", ...)
#   Request → Outline → Draft            reviewer = client.as_agent(name="reviewer", ...)
outliner.consumes(Request)
        .publishes(Outline)              workflow = (
writer.consumes(Outline)                     WorkflowBuilder(start_executor=writer)
      .publishes(Draft)                      .add_edge(writer, reviewer)
                                             .build()
# One publish cascades through all       )
await flock.publish(Request(...))
await flock.run_until_idle()             events = await workflow.run("input text")
                                         outputs = events.get_outputs()
```

## Parallel Execution

```python
# ── Flock (automatic) ────────────     # ── Agent Framework (fan-out/in) ───
# Same input type = parallel             from agent_framework import AgentExecutor
a.consumes(Input).publishes(ReportA)
b.consumes(Input).publishes(ReportB)     a = AgentExecutor(client.as_agent(...))
c.consumes(Input).publishes(ReportC)     b = AgentExecutor(client.as_agent(...))
                                         c = AgentExecutor(client.as_agent(...))
await flock.publish(Input(...))
await flock.run_until_idle()             workflow = (
# All 3 ran in parallel                     WorkflowBuilder(start_executor=dispatcher)
                                             .add_fan_out_edges(dispatcher, [a, b, c])
# AND-gate (wait for all):                   .add_fan_in_edges([a, b, c], aggregator)
merger.consumes(ReportA, ReportB,            .build()
               ReportC)                  )
```

## Conditional Routing

```python
# ── Flock (where= predicate) ─────    # ── Agent Framework (switch-case) ──
senior.consumes(                         workflow = (
    Ticket,                                  WorkflowBuilder(start_executor=classifier)
    where=lambda t: t.priority=="critical"   .add_switch_case_edge_group(
)                                                classifier,
standard.consumes(                               [
    Ticket,                                          Case(
    where=lambda t: t.priority=="normal"                 condition=lambda m: m.route == "senior",
)                                                        target=senior_handler,
                                                     ),
                                                     Default(target=standard_handler),
                                                 ],
                                             )
                                             .build()
                                         )
```

## Tools

```python
# ── Flock ──────────────────────────    # ── Agent Framework ────────────────
def get_weather(city: str) -> str:       from agent_framework import tool
    return f"{city}: sunny"              from typing import Annotated
                                         from pydantic import Field
agent = (
    flock.agent("planner")               @tool(approval_mode="never_require")
    .consumes(Request)                   def get_weather(
    .publishes(Plan)                         city: Annotated[str, Field(description="City name")],
    .tools(get_weather)                  ) -> str:
)                                            return f"{city}: sunny"

                                         agent = client.as_agent(
                                             name="planner",
                                             tools=[get_weather],
                                         )
```

## Custom Executors (Agent Framework only)

```python
from agent_framework import Executor, handler, executor, WorkflowContext
from typing_extensions import Never

# Class-based
class MyNode(Executor):
    @handler
    async def process(self, text: str, ctx: WorkflowContext[str]) -> None:
        await ctx.send_message(text.upper())       # send downstream

# Function-based
@executor(id="final")
async def final_node(text: str, ctx: WorkflowContext[Never, str]) -> None:
    await ctx.yield_output(text)                    # yield workflow output

# WorkflowContext type params:
#   WorkflowContext[T_Out]           → sends messages downstream
#   WorkflowContext[Never, T_WOut]   → yields workflow output only
#   WorkflowContext[T_Out, T_WOut]   → both
#   WorkflowContext                  → neither (terminal)
```

## Workflow State (Agent Framework only)

```python
# Set state (persists across nodes)
ctx.set_state("key", value)

# Get state
value = ctx.get_state("key")
```

## Environment Variables

```
# OpenAI mode
OPENAI_API_KEY=sk-...
DEFAULT_MODEL=openai/gpt-4.1
OPENAI_RESPONSES_MODEL_ID=gpt-4.1

# Azure mode (shared creds for both frameworks)
AZURE_API_KEY=...
AZURE_API_BASE=https://...cognitiveservices.azure.com/
AZURE_API_VERSION=2025-04-01-preview
DEFAULT_MODEL=azure/<deployment_name>
```

## Running Examples

```bash
uv run <module>/flock/<script>.py
uv run <module>/agent_framework/<script>.py
```
