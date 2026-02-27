"""
Module 02 - Multi-Agent Pipeline (Flock)

LEARNING OBJECTIVE:
Chain multiple agents into a sequential pipeline using Flock's type cascade pattern.
When Agent A publishes Type B, Agent B (which consumes Type B) triggers automatically.

KEY CONCEPTS:
- Type cascade: Agent A → Type B → Agent B → Type C → Agent C
- Each agent only knows its input and output types
- The pipeline emerges from type dependencies, not explicit wiring
- Adding a new stage = adding a new agent (zero changes to existing agents)
"""

import asyncio

from pydantic import BaseModel, Field

from flock import Flock
from flock.registry import flock_type


# ============================================================================
# STEP 1: Define the Artifact Types for a Content Pipeline
# ============================================================================
# We're building: Topic → Outline → Draft
#
# The type cascade creates a natural pipeline:
#   TopicRequest triggers the outliner
#   ContentOutline triggers the writer
#
# No agent knows about the others — they just react to their types.
# ============================================================================

@flock_type
class TopicRequest(BaseModel):
    """A request to create content about a topic."""
    topic: str = Field(description="The topic to write about")
    audience: str = Field(default="general", description="Target audience")
    word_count: int = Field(default=300, description="Target word count for the final draft")


@flock_type
class ContentOutline(BaseModel):
    """A structured outline for a piece of content."""
    topic: str = Field(description="The topic being outlined")
    audience: str = Field(description="Target audience")
    sections: list[str] = Field(description="List of section headings with brief descriptions")
    key_points: list[str] = Field(description="Key points to cover")
    word_count: int = Field(description="Target word count")


@flock_type
class ContentDraft(BaseModel):
    """A complete content draft."""
    title: str = Field(description="Article title")
    body: str = Field(description="The full article text")
    word_count: int = Field(description="Actual word count")
    summary: str = Field(description="One-paragraph summary")


# ============================================================================
# STEP 2: Create Orchestrator and Agents
# ============================================================================
# Two agents form a pipeline through their type declarations:
#   outliner: TopicRequest → ContentOutline
#   writer:   ContentOutline → ContentDraft
#
# The pipeline is IMPLICIT — it emerges from type matching.
# ============================================================================

flock = Flock()

outliner = (
    flock.agent("outliner")
    .description(
        "A content strategist who creates detailed outlines. "
        "Analyze the topic and audience, then produce a structured outline "
        "with clear sections and key points to cover."
    )
    .consumes(TopicRequest)
    .publishes(ContentOutline)
)

writer = (
    flock.agent("writer")
    .description(
        "A skilled content writer who turns outlines into polished articles. "
        "Follow the outline structure, hit the target word count, and write "
        "in a style appropriate for the target audience."
    )
    .consumes(ContentOutline)
    .publishes(ContentDraft)
)


# ============================================================================
# STEP 3: Run the Pipeline
# ============================================================================
# Publish a TopicRequest → outliner triggers → publishes ContentOutline →
# writer triggers → publishes ContentDraft
#
# All of this happens from a SINGLE publish + run_until_idle() call.
# ============================================================================

async def main():
    print("=" * 60)
    print("  Multi-Agent Pipeline — Flock (Type Cascade)")
    print("=" * 60)
    print()

    request = TopicRequest(
        topic="Why developers should learn about AI agent orchestration",
        audience="software developers",
        word_count=300,
    )

    print(f"  Topic: {request.topic}")
    print(f"  Audience: {request.audience}")
    print(f"  Target words: {request.word_count}")
    print()
    print("  Publishing topic request...")
    print("  (outliner and writer will cascade automatically)")
    print()

    await flock.publish(request)
    await flock.run_until_idle()

    # Check intermediate result (outline)
    outlines = await flock.store.get_by_type(ContentOutline)
    if outlines:
        outline = outlines[0]
        print("  OUTLINE (intermediate artifact):")
        print(f"  Sections: {len(outline.sections)}")
        for section in outline.sections:
            print(f"    - {section}")
        print()

    # Check final result (draft)
    drafts = await flock.store.get_by_type(ContentDraft)
    if drafts:
        draft = drafts[0]
        print(f"  FINAL DRAFT: {draft.title}")
        print(f"  Word count: {draft.word_count}")
        print(f"  Summary: {draft.summary}")
        print()
        print("  " + "-" * 40)
        # Print first 500 chars of body
        preview = draft.body[:500]
        for line in preview.split("\n"):
            print(f"  {line}")
        if len(draft.body) > 500:
            print("  [... truncated ...]")
        print("  " + "-" * 40)
    else:
        print("  No draft generated. Check your .env configuration.")

    print()
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())


# ============================================================================
# YOUR TURN!
# ============================================================================
#
# EXPERIMENT 1: Add a Third Stage
# Create a ContentReview type and a "reviewer" agent:
#   reviewer: ContentDraft → ContentReview
# Run the pipeline. Does it cascade through all three stages?
#
# EXPERIMENT 2: Inspect the Blackboard
# After run_until_idle(), check all artifact types:
#   topics = await flock.store.get_by_type(TopicRequest)
#   outlines = await flock.store.get_by_type(ContentOutline)
#   drafts = await flock.store.get_by_type(ContentDraft)
# Every intermediate artifact is preserved. Why is this useful?
#
# EXPERIMENT 3: Multiple Topics
# Publish 2 TopicRequests before run_until_idle().
# How many outlines and drafts are produced?
#
# COMPARE: After running the Agent Framework version, consider:
# - In Flock, how did you "wire" the pipeline? (You didn't — types did it)
# - In AF, how did you wire it? (Explicit .add_edge() calls)
# - Which approach would be easier to extend with new stages?
# ============================================================================
