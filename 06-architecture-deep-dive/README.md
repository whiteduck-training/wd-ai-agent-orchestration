# Module 06 — Architecture Deep Dive

> No code in this module — just the theory behind both architectures.

## The Blackboard Model (Flock)

### How the Blackboard Works Internally

```
                    ┌─────────────────────────────────────┐
                    │         BLACKBOARD (Store)           │
                    │                                      │
  publish(A) ──────►│  ┌───┐  ┌───┐  ┌───┐  ┌───┐       │
                    │  │ A │  │ B │  │ C │  │ D │       │
                    │  └─┬─┘  └─┬─┘  └─┬─┘  └───┘       │
                    └────┼──────┼──────┼──────────────────┘
                         │      │      │
                    ┌────▼──────▼──────▼──────────────────┐
                    │       SUBSCRIPTION MATCHER           │
                    │                                      │
                    │  Agent1.consumes(A) ──► MATCH ✓      │
                    │  Agent2.consumes(B) ──► MATCH ✓      │
                    │  Agent3.consumes(A,B) ─► WAIT (B?)   │
                    │  Agent4.consumes(C) ──► MATCH ✓      │
                    └────┬──────┬──────┬──────────────────┘
                         │      │      │
                    ┌────▼──────▼──────▼──────────────────┐
                    │       EXECUTION ENGINE                │
                    │                                      │
                    │  [Agent1] ──► running (parallel)     │
                    │  [Agent2] ──► running (parallel)     │
                    │  [Agent4] ──► running (parallel)     │
                    │  [Agent3] ──► blocked (waiting B)    │
                    └──────────────────────────────────────┘
```

### The Execution Cycle

1. **Publish**: An artifact is placed on the blackboard
2. **Match**: The subscription matcher checks all agents' `consumes()` declarations
3. **Filter**: `where=` predicates further filter which agents activate
4. **AND-gate**: Agents consuming multiple types only activate when ALL types are present
5. **Execute**: All matched agents run concurrently
6. **Cascade**: Output artifacts trigger another matching cycle
7. **Idle**: When no more agents are triggered, `run_until_idle()` returns

### Key Insight: Emergence

The execution order is **emergent** — it's not programmed anywhere. It arises from:
- What types are on the blackboard
- What types each agent consumes
- What types each agent publishes
- When artifacts appear

This means the same set of agents can produce different execution orders depending on what data is published and when.

---

## The DAG / Superstep Model (Agent Framework)

### How the Graph Executes

```
  Superstep 0              Superstep 1              Superstep 2
  ┌──────────┐
  │  Start   │
  │  Node    │──────┐
  └──────────┘      │
                    ▼
              ┌──────────┐
              │ Fan-Out  │
              └──┬──┬──┬─┘
                 │  │  │
     ┌───────────┘  │  └───────────┐
     ▼              ▼              ▼
  ┌──────┐     ┌──────┐     ┌──────┐
  │Node A│     │Node B│     │Node C│
  └──┬───┘     └──┬───┘     └──┬───┘
     │             │             │
     └──────┬──────┘─────────────┘
            ▼
      ┌──────────┐
      │ Fan-In   │  ← waits for A, B, C
      │(Barrier) │
      └──┬───────┘
         │
         ▼
      ┌──────────┐
      │Aggregator│
      └──────────┘
```

### Superstep Mechanics

Borrowed from Google's **Pregel** paper (2010), supersteps work like this:

1. **Superstep 0**: Start node receives input, processes it, sends messages along edges
2. **Barrier**: All messages from superstep 0 must be delivered before superstep 1 begins
3. **Superstep 1**: All nodes that received messages process them concurrently
4. **Fan-In Barrier**: If a node has fan-in edges, it waits for ALL sources to deliver
5. **Superstep 2**: Aggregation nodes process collected messages
6. **Terminal**: Nodes with `yield_output()` produce workflow results

### Key Insight: Determinism

The execution order is **deterministic** — given the same graph and input:
- The same nodes will execute in the same order
- Fan-out always broadcasts to all targets
- Fan-in always waits for all sources
- Switch-case evaluates predicates in declaration order

This makes debugging and auditing straightforward: you can trace exactly which path was taken and why.

---

## Comparison: 12 Dimensions

| Dimension | Blackboard (Flock) | DAG (Agent Framework) |
|-----------|-------------------|----------------------|
| **1. Coupling** | Loose — agents only know types | Tight — edges define relationships |
| **2. Execution order** | Emergent from data | Determined by graph topology |
| **3. Parallelism** | Automatic (same input type) | Explicit (fan-out edges) |
| **4. Synchronization** | AND-gate on types | Fan-in barrier on edges |
| **5. Conditional routing** | Decentralized (`where=`) | Centralized (switch-case) |
| **6. State** | Blackboard (all artifacts visible) | WorkflowContext (scoped state dict) |
| **7. Debugging** | Watch artifacts appear | Trace graph edges |
| **8. Extensibility** | Add agent = new subscription | Add node + wire edges |
| **9. Determinism** | Non-deterministic order | Fully deterministic |
| **10. Visualization** | Built-in dashboard | Graph structure IS the visualization |
| **11. Error propagation** | Agent failure = missing output | Node failure = graph halt |
| **12. Mental model** | "Publish and react" | "Flow through pipeline" |

---

## Historical Parallels

### Blackboard Pattern

| System | Year | Domain |
|--------|------|--------|
| Hearsay-II | 1977 | Speech recognition |
| BB1 | 1986 | General-purpose AI |
| GBB | 1988 | Knowledge systems |
| Actor Model (Erlang) | 1986+ | Concurrent systems |
| Event-driven microservices | 2010s+ | Distributed systems |
| **Flock** | 2024+ | AI agent orchestration |

### DAG / Workflow Pattern

| System | Year | Domain |
|--------|------|--------|
| Make/Build systems | 1976 | Software build automation |
| Dataflow architecture | 1980s | Computer architecture |
| MapReduce | 2004 | Distributed data processing |
| Pregel | 2010 | Graph processing |
| Apache Airflow | 2014 | Workflow orchestration |
| TensorFlow | 2015 | ML computation graphs |
| **Agent Framework** | 2024+ | AI agent orchestration |

---

## The Hybrid Approach

In practice, many production systems combine both:

```
┌─────────────────────────────────────────┐
│          DAG Pipeline (Outer)            │
│                                          │
│  ┌────────┐    ┌────────────┐    ┌────┐ │
│  │ Intake  │───►│ Processing │───►│ QA │ │
│  └────────┘    └──────┬─────┘    └────┘ │
│                       │                  │
│                ┌──────▼──────┐           │
│                │  Blackboard  │           │
│                │  (Inner)     │           │
│                │  Agent A ◄──►│           │
│                │  Agent B ◄──►│           │
│                │  Agent C ◄──►│           │
│                └─────────────┘           │
└─────────────────────────────────────────┘
```

- The **outer DAG** provides deterministic pipeline stages
- The **inner blackboard** provides flexible agent collaboration within a stage
- Best of both: auditable pipeline + adaptive intelligence

## Next

[Module 07 — Advanced Patterns](../07-advanced-patterns/) — fan-out/join, feedback loops, and more.
