# Module 08 — When to Use Which

> A practical decision framework for choosing between blackboard and DAG architectures.

## The Decision Flowchart

```
START: What kind of system are you building?
│
├─► "I need predictable, auditable execution"
│   └─► Agent Framework (DAG)
│
├─► "I need rapid prototyping with evolving requirements"
│   └─► Flock (Blackboard)
│
├─► "I need both predictability AND flexibility"
│   └─► Hybrid (DAG outer, Blackboard inner)
│
└─► "I'm not sure yet"
    │
    ├─► Do you know the exact workflow steps upfront?
    │   ├─► YES → Agent Framework
    │   └─► NO  → Flock
    │
    ├─► Will agents be added/removed frequently?
    │   ├─► YES → Flock
    │   └─► NO  → Agent Framework
    │
    ├─► Do you need to audit every execution path?
    │   ├─► YES → Agent Framework
    │   └─► NO  → Either works
    │
    └─► Is this a plugin/extension system?
        ├─► YES → Flock
        └─► NO  → Evaluate both
```

## Scenario Analysis

### Scenario 1: Customer Support Automation

**Situation**: Route tickets to specialists, escalate when needed, track SLAs.

| Factor | Assessment |
|--------|-----------|
| Workflow known? | Yes — well-defined routing rules |
| Audit needed? | Yes — SLA compliance tracking |
| Agents change? | Rarely — stable set of specialists |
| Verdict | **Agent Framework** — deterministic routing, auditable paths |

### Scenario 2: Content Creation Pipeline

**Situation**: Research, write, review, publish. Writers and reviewers change often.

| Factor | Assessment |
|--------|-----------|
| Workflow known? | Roughly — but steps evolve |
| Audit needed? | Not critical |
| Agents change? | Often — new writers, reviewers, fact-checkers |
| Verdict | **Flock** — easy to add/remove agents, types define the flow |

### Scenario 3: Financial Compliance Checks

**Situation**: Transaction screening through multiple compliance checks.

| Factor | Assessment |
|--------|-----------|
| Workflow known? | Yes — regulatory requirements are specific |
| Audit needed? | Absolutely — regulatory compliance |
| Agents change? | When regulations change (infrequent) |
| Verdict | **Agent Framework** — deterministic, auditable, compliant |

### Scenario 4: Research Assistant

**Situation**: Search, summarize, cross-reference, fact-check. Tools and sources change.

| Factor | Assessment |
|--------|-----------|
| Workflow known? | No — depends on the query |
| Audit needed? | Helpful but not critical |
| Agents change? | Frequently — new tools, sources, methods |
| Verdict | **Flock** — emergent workflows adapt to different queries |

### Scenario 5: CI/CD Pipeline

**Situation**: Build, test, scan, deploy. Fixed stages with parallelism.

| Factor | Assessment |
|--------|-----------|
| Workflow known? | Yes — well-defined build pipeline |
| Audit needed? | Yes — deployment audit trail |
| Agents change? | Rarely |
| Verdict | **Agent Framework** — explicit graph, fan-out for parallel tests |

### Scenario 6: Creative AI Studio

**Situation**: Multiple AI agents collaborate on creative projects — brainstorming, drafting, critiquing.

| Factor | Assessment |
|--------|-----------|
| Workflow known? | No — creative process is emergent |
| Audit needed? | No |
| Agents change? | Constantly — experimentation |
| Verdict | **Flock** — blackboard enables emergent creative collaboration |

## Quick Reference Matrix

| Use Case | Flock | Agent Framework | Hybrid |
|----------|:-----:|:---------------:|:------:|
| Prototyping / MVPs | Best | Good | Overkill |
| Regulatory compliance | Risky | Best | Good |
| Plugin architecture | Best | Poor | Good |
| Fixed pipeline | Good | Best | Overkill |
| Creative/exploratory | Best | Poor | Good |
| Real-time dashboards | Best (built-in) | Manual | Manual |
| CI/CD-style workflows | Good | Best | Good |
| Evolving requirements | Best | Verbose | Good |
| Auditable execution | Challenging | Best | Good |
| Team of specialists | Best | Good | Best |

## Team Fit

### Choose Flock When Your Team...

- Values rapid iteration and experimentation
- Is comfortable with event-driven thinking
- Wants to add capabilities without touching existing code
- Needs built-in observability (dashboard)
- Is building creative or exploratory AI systems

### Choose Agent Framework When Your Team...

- Needs to reason about execution order
- Values explicit, visible architecture
- Requires audit trails and compliance
- Wants deterministic, reproducible behavior
- Is building production pipelines

### Consider Hybrid When Your Team...

- Has both structured pipelines and flexible stages
- Needs outer predictability with inner adaptability
- Is building large systems with multiple subsystems
- Wants the best of both approaches

## The Hybrid Pattern

```python
# Outer: Agent Framework DAG for structured pipeline
workflow = (
    WorkflowBuilder(start_executor=intake)
    .add_edge(intake, processing_stage)  # Fixed pipeline
    .add_edge(processing_stage, quality_check)
    .build()
)

# Inner: Flock blackboard for flexible processing
# (Inside the processing_stage executor)
async def process(self, data, ctx):
    flock = Flock()
    # Dynamic agents based on data type
    flock.agent("analyzer").consumes(DataType).publishes(Analysis)
    await flock.publish(data)
    await flock.run_until_idle()
    results = await flock.store.get_by_type(Analysis)
    await ctx.send_message(results)
```

This gives you:
- **Deterministic outer pipeline** — auditable, predictable stages
- **Flexible inner processing** — agents adapt to different data types
- **Best of both** — structure where needed, flexibility where valuable

## Final Thoughts

There's no universally "better" architecture. The right choice depends on:

1. **Your requirements** — Do you need auditability? Flexibility? Both?
2. **Your team** — What mental model does your team think in?
3. **Your timeline** — Need an MVP fast? Blackboard. Need production reliability? DAG.
4. **Your system's evolution** — Will it change often? Blackboard. Is it stable? DAG.

The fact that you now understand both architectures means you can make an **informed decision** — and that's the real superpower.

## Workshop Complete!

Congratulations! You've built agents in both frameworks, compared their architectures side by side, and now have a decision framework for choosing the right approach.

**What to explore next**:
- Build a real project using your chosen framework
- Try the hybrid approach for a complex system
- Contribute to either framework's open source community
- Check the [ARCHITECTURE.md](../ARCHITECTURE.md) for deeper theory
