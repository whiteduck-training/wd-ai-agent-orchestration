"""
Module 03 - Parallel Execution (Agent Framework)

LEARNING OBJECTIVE:
Use fan-out and fan-in edges to run multiple agents in parallel
and aggregate their results.

KEY CONCEPTS:
- .add_fan_out_edges(source, [targets]) broadcasts to multiple agents
- .add_fan_in_edges([sources], target) waits for ALL sources, then aggregates
- Fan-in target receives a list of all responses
- Explicit parallelism = visible, controllable, deterministic
"""

import asyncio
from dataclasses import dataclass
from typing import cast

from dotenv import load_dotenv
from typing_extensions import Never

from agent_framework import (
    AgentExecutor,
    AgentExecutorRequest,
    AgentExecutorResponse,
    Executor,
    Message,
    WorkflowBuilder,
    WorkflowContext,
    handler,
)
from agent_framework.openai import OpenAIResponsesClient


# ============================================================================
# STEP 1: Create the Dispatcher (Entry Point)
# ============================================================================
# The dispatcher is a custom Executor that takes the user's input
# and formats it as a request for the parallel agents.
#
# It sends the SAME message to all downstream targets via fan-out.
# ============================================================================

load_dotenv()


class DispatchToAnalysts(Executor):
    """Receives user input and dispatches to all analyst agents."""

    @handler
    async def dispatch(self, prompt: str, ctx: WorkflowContext[AgentExecutorRequest]) -> None:
        initial_message = Message("user", text=prompt)
        await ctx.send_message(
            AgentExecutorRequest(messages=[initial_message], should_respond=True)
        )


# ============================================================================
# STEP 2: Create the Aggregator (Fan-In Target)
# ============================================================================
# The aggregator receives a LIST of responses from all parallel agents.
# Fan-in waits for ALL sources to complete before triggering.
#
# This is the synchronized join — no results are lost.
# ============================================================================

@dataclass
class AnalysisReport:
    market: str
    technical: str
    customer: str


class AggregateAnalyses(Executor):
    """Collects all analyst responses and produces a combined report."""

    @handler
    async def aggregate(
        self, results: list[AgentExecutorResponse], ctx: WorkflowContext[Never, str]
    ) -> None:
        # results is a list — one entry per parallel agent
        by_agent: dict[str, str] = {}
        for r in results:
            by_agent[r.executor_id] = r.agent_response.text or "(no response)"

        report = (
            "COMBINED ANALYSIS REPORT\n"
            "========================\n\n"
            f"MARKET ANALYSIS:\n{by_agent.get('market_analyst', 'N/A')}\n\n"
            f"TECHNICAL REVIEW:\n{by_agent.get('tech_reviewer', 'N/A')}\n\n"
            f"CUSTOMER INSIGHT:\n{by_agent.get('customer_researcher', 'N/A')}"
        )

        await ctx.yield_output(report)


# ============================================================================
# STEP 3: Create Agents and Build the Workflow
# ============================================================================
# The graph structure:
#   dispatcher → [market, tech, customer]  (fan-out: parallel)
#   [market, tech, customer] → aggregator  (fan-in: synchronized join)
#
# This is EXPLICIT parallelism — you declare exactly which agents
# run in parallel and how results are collected.
# ============================================================================

client = OpenAIResponsesClient()

market_agent = AgentExecutor(
    client.as_agent(
        name="market_analyst",
        instructions=(
            "You are a market analyst. Evaluate the product's market positioning, "
            "identify 3 key competitors, and rate the market opportunity from 1-10. "
            "Be concise — 3-4 sentences."
        ),
    )
)

tech_agent = AgentExecutor(
    client.as_agent(
        name="tech_reviewer",
        instructions=(
            "You are a technical reviewer. Assess the product's technical feasibility, "
            "identify 3 implementation risks, and rate complexity from 1-10. "
            "Be concise — 3-4 sentences."
        ),
    )
)

customer_agent = AgentExecutor(
    client.as_agent(
        name="customer_researcher",
        instructions=(
            "You are a customer researcher. Identify the target persona, "
            "list 3 pain points this product addresses, and rate appeal from 1-10. "
            "Be concise — 3-4 sentences."
        ),
    )
)

dispatcher = DispatchToAnalysts(id="dispatcher")
aggregator = AggregateAnalyses(id="aggregator")

workflow = (
    WorkflowBuilder(start_executor=dispatcher)
    .add_fan_out_edges(dispatcher, [market_agent, tech_agent, customer_agent])
    .add_fan_in_edges([market_agent, tech_agent, customer_agent], aggregator)
    .build()
)


# ============================================================================
# STEP 4: Run the Workflow
# ============================================================================

async def main():
    print("=" * 60)
    print("  Parallel Execution — Agent Framework (Fan-Out/Fan-In)")
    print("=" * 60)
    print()

    product_description = (
        "Product: SmartGarden Pro\n"
        "Description: An AI-powered indoor garden that automatically adjusts light, water, and nutrients\n"
        "Price: $299.99\n"
        "Category: Smart Home / IoT"
    )

    print("  Product: SmartGarden Pro ($299.99)")
    print()
    print("  Running workflow: dispatcher → [market, tech, customer] → aggregator")
    print("  (3 agents running in PARALLEL with explicit fan-out)")
    print()

    events = await workflow.run(product_description)
    outputs = events.get_outputs()

    if outputs:
        report = str(outputs[0])
        for line in report.split("\n"):
            print(f"  {line}")
    else:
        print("  No output. Check your .env configuration.")

    print()
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())


# ============================================================================
# YOUR TURN!
# ============================================================================
#
# EXPERIMENT 1: Add a Fourth Analyst
# Create a financial_agent and add it to both fan-out and fan-in:
#   .add_fan_out_edges(dispatcher, [market, tech, customer, financial])
#   .add_fan_in_edges([market, tech, customer, financial], aggregator)
# Update the aggregator to handle the new agent.
#
# EXPERIMENT 2: Streaming Results
# Replace workflow.run() with:
#   async for event in workflow.run(product, stream=True):
# Print events as they arrive. Which agent finishes first?
#
# EXPERIMENT 3: Selective Fan-Out
# What if you only want 2 of the 3 agents? Just change the arrays.
# In Flock, how would you achieve the same selectivity?
#
# COMPARE: After running the Flock version, consider:
# - Flock: parallelism is automatic (same input type)
# - AF: parallelism is explicit (fan-out edges)
# - Adding a 4th analyst: Flock = add agent; AF = add agent + update edges
# - Which gives you more control? Which is faster to extend?
# ============================================================================
