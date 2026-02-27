"""
Module 01 - Hello Agent (Flock)

LEARNING OBJECTIVE:
Build your first Flock agent and understand the blackboard pattern:
typed artifacts published to a shared store trigger agents automatically.

KEY CONCEPTS:
- @flock_type registers Pydantic models as artifact types
- .agent().consumes().publishes() declares an agent's data contract
- flock.publish() puts data on the blackboard
- flock.run_until_idle() runs all triggered agents to completion
"""

import asyncio

from pydantic import BaseModel, Field

from flock import Flock
from flock.registry import flock_type


# ============================================================================
# STEP 1: Define Your Artifact Types
# ============================================================================
# In Flock, all data is typed. You define Pydantic models that represent
# the data flowing through your system. The @flock_type decorator registers
# them with the blackboard so agents can subscribe to them.
#
# Think of these as "event types" — when one appears on the blackboard,
# any agent that consumes it will be triggered automatically.
# ============================================================================

@flock_type
class PoemRequest(BaseModel):
    """A request to generate a poem."""
    topic: str = Field(description="The topic or theme of the poem")
    style: str = Field(default="free verse", description="Poetry style (e.g., haiku, sonnet, free verse)")


@flock_type
class Poem(BaseModel):
    """A generated poem."""
    title: str = Field(description="Title of the poem")
    text: str = Field(description="The poem text")
    style: str = Field(description="The style used")


# ============================================================================
# STEP 2: Create the Orchestrator
# ============================================================================
# Flock() creates the orchestrator that manages the blackboard and agents.
# It reads DEFAULT_MODEL from your .env file to know which LLM to use.
# ============================================================================

flock = Flock()


# ============================================================================
# STEP 3: Declare Your Agent
# ============================================================================
# The fluent API makes agent declaration very readable:
#   .agent("name")       — unique identifier
#   .description("...")   — instructions for the LLM
#   .consumes(Type)       — what triggers this agent
#   .publishes(Type)      — what this agent produces
#
# The agent does NOT know about any other agent. It only knows:
# "When I see a PoemRequest, I should produce a Poem."
# ============================================================================

poet_agent = (
    flock.agent("poet")
    .description(
        "A creative poet who writes beautiful poems. "
        "Given a topic and style, craft an evocative poem with a fitting title."
    )
    .consumes(PoemRequest)
    .publishes(Poem)
)


# ============================================================================
# STEP 4: Run the System
# ============================================================================
# The execution pattern is always the same:
# 1. Publish artifact(s) to the blackboard
# 2. Run until all triggered agents finish
# 3. Retrieve results by type from the blackboard
# ============================================================================

async def main():
    print("=" * 60)
    print("  Hello Agent — Flock (Blackboard Architecture)")
    print("=" * 60)
    print()

    # Create a poem request
    request = PoemRequest(
        topic="the beauty of open source collaboration",
        style="free verse",
    )

    print(f"  Topic: {request.topic}")
    print(f"  Style: {request.style}")
    print()
    print("  Publishing request to blackboard...")
    print()

    # Publish to blackboard — this triggers the poet agent
    await flock.publish(request)

    # Run until the agent finishes
    await flock.run_until_idle()

    # Retrieve the result from the blackboard
    poems = await flock.store.get_by_type(Poem)

    if poems:
        poem = poems[0]
        print(f"  {poem.title}")
        print(f"  {'—' * len(poem.title)}")
        print()
        for line in poem.text.split("\n"):
            print(f"  {line}")
        print()
        print(f"  Style: {poem.style}")
    else:
        print("  No poem generated. Check your OPENAI_API_KEY in .env")

    print()
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())


# ============================================================================
# YOUR TURN!
# ============================================================================
#
# EXPERIMENT 1: Different Topics
# Change the topic to something you care about and run again.
#
# EXPERIMENT 2: Different Styles
# Try style="haiku", style="sonnet", or style="limerick".
# How does the output change?
#
# EXPERIMENT 3: Multiple Requests
# Publish 3 PoemRequest artifacts before calling run_until_idle().
# How many poems are generated? Why?
#
# EXPERIMENT 4: Agent Description Matters
# Change the poet's description to:
#   "A minimalist poet who uses only 10 words per poem"
# Run again. What changes?
#
# COMPARE: After running the Agent Framework version, consider:
# - Which approach made the agent's behavior more obvious?
# - Which was easier to modify?
# - Where is the "intelligence" — in the types or the instructions?
# ============================================================================
