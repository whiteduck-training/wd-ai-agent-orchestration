"""
Module 02 - Multi-Agent Pipeline (Agent Framework)

LEARNING OBJECTIVE:
Chain multiple agents into a sequential pipeline using explicit graph edges.
WorkflowBuilder.add_edge() creates a directed connection between agents.

KEY CONCEPTS:
- WorkflowBuilder defines the execution graph
- .add_edge(source, target) connects two agents sequentially
- Agents pass messages along edges automatically
- The graph is visible and deterministic
"""

import asyncio
from typing import cast

from dotenv import load_dotenv

from agent_framework import AgentResponse, WorkflowBuilder
from agent_framework.openai import OpenAIResponsesClient


# ============================================================================
# STEP 1: Create Client and Agents
# ============================================================================
# We create two agents with clear, distinct roles:
#   - outliner: takes a topic and produces a structured outline
#   - writer: takes an outline and produces a polished draft
#
# Each agent gets natural language instructions describing its job.
# ============================================================================

load_dotenv()

client = OpenAIResponsesClient()

outliner_agent = client.as_agent(
    name="outliner",
    instructions=(
        "You are a content strategist. Given a topic and audience, create a detailed outline. "
        "Format your response as a structured outline with numbered sections and key points."
    ),
)

writer_agent = client.as_agent(
    name="writer",
    instructions=(
        "You are a skilled content writer. You receive an outline from a content strategist. "
        "Turn it into a polished, well-written article of approximately 300 words. "
        "Follow the outline structure closely. End with a one-paragraph summary."
    ),
)


# ============================================================================
# STEP 2: Build the Workflow Graph
# ============================================================================
# WorkflowBuilder creates a directed graph:
#   outliner → writer
#
# The start_executor is the entry point — it receives the initial message.
# add_edge() connects the outliner's output to the writer's input.
#
# This is EXPLICIT wiring — you can see the entire pipeline at a glance.
# ============================================================================

workflow = (
    WorkflowBuilder(start_executor=outliner_agent)
    .add_edge(outliner_agent, writer_agent)
    .build()
)


# ============================================================================
# STEP 3: Run the Workflow
# ============================================================================
# workflow.run(message) sends the message to the start node and
# follows the graph until completion.
#
# The result contains outputs from the terminal nodes (writer, in this case).
# ============================================================================

async def main():
    print("=" * 60)
    print("  Multi-Agent Pipeline — Agent Framework (Explicit Graph)")
    print("=" * 60)
    print()

    topic = "Why developers should learn about AI agent orchestration"
    audience = "software developers"

    print(f"  Topic: {topic}")
    print(f"  Audience: {audience}")
    print()
    print("  Running workflow: outliner → writer")
    print()

    events = await workflow.run(
        f"Create content about: {topic}\nTarget audience: {audience}\nTarget length: ~300 words"
    )

    # Get the final outputs (from the terminal node — the writer)
    outputs = cast(list[AgentResponse], events.get_outputs())

    if outputs:
        for output in outputs:
            author = output.messages[0].author_name if output.messages else "writer"
            print(f"  RESULT from [{author}]:")
            print("  " + "-" * 40)
            text = output.text or ""
            # Print first 500 chars
            preview = text[:500]
            for line in preview.split("\n"):
                print(f"  {line}")
            if len(text) > 500:
                print("  [... truncated ...]")
            print("  " + "-" * 40)
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
# EXPERIMENT 1: Add a Reviewer Stage
# Create a reviewer_agent and add it to the workflow:
#   .add_edge(writer_agent, reviewer_agent)
# What does the reviewer receive as input?
#
# EXPERIMENT 2: Three-Agent Chain
# Use .add_chain([outliner_agent, writer_agent, reviewer_agent])
# instead of multiple .add_edge() calls. Same result, cleaner syntax.
#
# EXPERIMENT 3: Intermediate Output
# Change the workflow to get output from BOTH the outliner and writer.
# Hint: Use output_executors parameter in WorkflowBuilder.
#
# COMPARE: After running the Flock version, consider:
# - Flock's pipeline emerged from types — no .add_edge() needed.
# - AF's pipeline is explicitly wired — you can see the full graph.
# - Which approach is easier to reason about? To extend? To debug?
# ============================================================================
