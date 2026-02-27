# Architecture: Blackboard vs DAG

> Understanding the two fundamental approaches to multi-agent orchestration.

## Table of Contents

- [The Blackboard Architecture](#the-blackboard-architecture)
- [The DAG / Superstep Architecture](#the-dag--superstep-architecture)
- [Side-by-Side Comparison](#side-by-side-comparison)
- [Code Pattern Comparison](#code-pattern-comparison)
- [When Each Shines](#when-each-shines)

---

## The Blackboard Architecture

### History

The blackboard model originated with the **Hearsay-II** speech recognition system (1970s, Carnegie Mellon). Multiple "knowledge sources" (specialists) independently read from and write to a shared data structure — the blackboard. No specialist knows about any other; they only know what data types they can read and what they produce.

### How It Works

```
┌─────────────────────────────────────────────┐
│               BLACKBOARD                     │
│                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Artifact  │  │ Artifact  │  │ Artifact  │  │
│  │ Type A    │  │ Type B    │  │ Type C    │  │
│  └──────────┘  └──────────┘  └──────────┘  │
└──────┬──────────────┬──────────────┬────────┘
       │              │              │
  ┌────▼────┐   ┌─────▼────┐  ┌─────▼────┐
  │ Agent 1  │   │ Agent 2  │  │ Agent 3  │
  │ A → B    │   │ B → C    │  │ A → C    │
  └─────────┘   └──────────┘  └──────────┘
```

1. **Artifacts** are published to the blackboard (typed Pydantic models)
2. **Agents** declare what types they consume and produce
3. The **orchestrator** matches artifacts to agents and triggers execution
4. Agents run **automatically** when their input types appear
5. New artifacts may trigger **additional agents** — creating cascading execution

### Key Properties

- **Loose coupling** — agents don't know about each other
- **Automatic parallelism** — multiple agents triggered by the same artifact run concurrently
- **Emergent workflows** — execution order emerges from data dependencies
- **Easy evolution** — add/remove agents without changing existing ones

### In Flock

```python
# Agents declare types, not connections
flock.agent("writer").consumes(Topic).publishes(Draft)
flock.agent("reviewer").consumes(Draft).publishes(Review)
flock.agent("editor").consumes(Draft, Review).publishes(FinalDraft)

# Publish data — agents trigger automatically
await flock.publish(Topic(name="AI Safety"))
await flock.run_until_idle()
```

---

## The DAG / Superstep Architecture

### History

The directed acyclic graph (DAG) model draws from **workflow engines** (Apache Airflow), **dataflow programming** (TensorFlow), and Google's **Pregel** graph processing model (2010). Nodes are processing steps, edges define data flow. Execution follows the graph topology with synchronized phases (supersteps).

### How It Works

```
  ┌──────────┐
  │  Start    │
  │  Node     │
  └─────┬────┘
        │
   ┌────▼────┐
   │ Agent A  │
   └────┬────┘
        │
   ┌────▼──────────────┐
   │   Fan-Out          │
   ├────┬────┬─────────┤
   ▼    ▼    ▼         │
  ┌──┐ ┌──┐ ┌──┐      │
  │B1│ │B2│ │B3│      │
  └──┘ └──┘ └──┘      │
   │    │    │         │
   ├────┴────┤         │
   │  Fan-In │         │
   └────┬────┘         │
        │              │
   ┌────▼────┐         │
   │Aggregator│         │
   └─────────┘         │
```

1. **Nodes** (executors) are defined with explicit handler methods
2. **Edges** connect nodes in a directed graph
3. **Messages** flow along edges from source to target
4. **Fan-out** broadcasts to multiple nodes; **fan-in** waits for all to complete
5. **Switch-case** edges route conditionally based on predicates

### Key Properties

- **Explicit topology** — you can see the entire execution graph
- **Deterministic execution** — same inputs always follow the same path
- **Synchronized phases** — fan-in waits for all branches before proceeding
- **Easy debugging** — trace execution through known graph edges

### In Agent Framework

```python
# Nodes are connected by explicit edges
workflow = (
    WorkflowBuilder(start_executor=writer_agent)
    .add_edge(writer_agent, reviewer_agent)
    .add_edge(reviewer_agent, editor_agent)
    .build()
)

# Run follows the graph
events = await workflow.run("Write about AI Safety")
```

---

## Side-by-Side Comparison

| Dimension | Blackboard (Flock) | DAG (Agent Framework) |
|-----------|-------------------|----------------------|
| **Coupling** | Loose — agents only know types | Tight — edges define connections |
| **Parallelism** | Automatic — emerges from type matching | Explicit — fan-out edges |
| **Execution order** | Emergent from data flow | Determined by graph topology |
| **Adding agents** | Drop in, declare types | Add node + wire edges |
| **Debugging** | Watch the blackboard | Trace the graph |
| **Determinism** | Less predictable order | Fully deterministic paths |
| **Conditional routing** | `where=` predicates on types | `Case`/`Default` edge groups |
| **State management** | Artifacts on blackboard | `WorkflowContext` state dict |
| **Visualization** | Built-in dashboard (port 8344) | Graph structure is the visualization |
| **Error handling** | Agent-level failures | Node-level with workflow state |
| **Scalability model** | Add more agents to blackboard | Add more nodes/edges to graph |
| **Mental model** | "Agents react to events" | "Data flows through a pipeline" |

---

## Code Pattern Comparison

### Defining an Agent

**Flock (Blackboard)**
```python
@flock_type
class Input(BaseModel):
    text: str

@flock_type
class Output(BaseModel):
    result: str

agent = flock.agent("worker").consumes(Input).publishes(Output)
```

**Agent Framework (DAG)**
```python
client = OpenAIResponsesClient()
agent = client.as_agent(
    name="worker",
    instructions="Process the input text.",
)
```

### Running a Pipeline

**Flock** — publish and let agents cascade:
```python
await flock.publish(Input(text="hello"))
await flock.run_until_idle()
results = await flock.store.get_by_type(Output)
```

**Agent Framework** — build graph and run:
```python
workflow = WorkflowBuilder(start_executor=agent_a).add_edge(agent_a, agent_b).build()
events = await workflow.run("hello")
outputs = events.get_outputs()
```

### Parallel Execution

**Flock** — automatic when multiple agents consume the same type:
```python
flock.agent("analyst_1").consumes(Data).publishes(Report)
flock.agent("analyst_2").consumes(Data).publishes(Report)
# Both trigger when Data is published
```

**Agent Framework** — explicit fan-out:
```python
workflow = (
    WorkflowBuilder(start_executor=dispatcher)
    .add_fan_out_edges(dispatcher, [analyst_1, analyst_2])
    .add_fan_in_edges([analyst_1, analyst_2], aggregator)
    .build()
)
```

---

## When Each Shines

### Choose Blackboard (Flock) When...

- Requirements are evolving and agents will be added/removed frequently
- You want automatic parallelism without explicit wiring
- The system should be extensible by third parties (plugin architecture)
- You're building exploratory or creative AI workflows
- You value rapid prototyping and iteration speed

### Choose DAG (Agent Framework) When...

- You need deterministic, auditable execution paths
- The workflow has clear, well-defined stages
- You need synchronized phases (wait for all X before proceeding)
- Compliance or debugging requires traceable data flow
- You're building production pipelines with predictable behavior

### They're Not Mutually Exclusive

In practice, many systems combine both: a DAG for the overall pipeline structure with blackboard-style flexibility within individual stages. Understanding both gives you the vocabulary to choose — or blend — the right approach for each problem.
