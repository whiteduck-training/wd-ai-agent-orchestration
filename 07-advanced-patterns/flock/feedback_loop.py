"""
Module 07 - Feedback Loop (Flock)

LEARNING OBJECTIVE:
Implement a self-improving loop where an agent's output feeds back as
input for another iteration, with a break condition.

KEY CONCEPTS:
- An agent can publish the SAME type it consumes (self-referential loop)
- where= predicates control when to continue vs stop
- The loop breaks when the predicate no longer matches
- This creates iterative refinement without explicit loop constructs
"""

import asyncio

from pydantic import BaseModel, Field

from flock import Flock
from flock.registry import flock_type


# ============================================================================
# STEP 1: Define Types for Iterative Essay Refinement
# ============================================================================
# An EssayDraft has an iteration counter and a quality score.
# The refiner agent consumes drafts that are below quality threshold
# and publishes improved versions (still EssayDraft type).
#
# The loop stops when quality >= threshold (where= no longer matches).
# ============================================================================

@flock_type
class EssayDraft(BaseModel):
    """An essay draft with quality tracking."""
    topic: str = Field(description="Essay topic")
    content: str = Field(description="The essay text")
    iteration: int = Field(description="Current iteration number (starts at 0)")
    quality_score: int = Field(description="Self-assessed quality score 1-10")
    feedback: str = Field(default="", description="Feedback from previous iteration")


QUALITY_THRESHOLD = 7
MAX_ITERATIONS = 3


# ============================================================================
# STEP 2: Create the Feedback Loop
# ============================================================================
# The refiner agent:
#   - Consumes EssayDraft WHERE quality < threshold AND iteration < max
#   - Publishes EssayDraft (same type — creates the loop)
#
# The loop AUTOMATICALLY stops when:
#   - quality >= QUALITY_THRESHOLD, OR
#   - iteration >= MAX_ITERATIONS
# because the where= predicate no longer matches.
# ============================================================================

flock = Flock()

refiner = (
    flock.agent("refiner")
    .description(
        f"An editor who improves essay drafts. Read the current draft and its feedback, "
        f"then produce an improved version. Be self-critical: score quality 1-10 honestly. "
        f"Target quality: {QUALITY_THRESHOLD}/10. "
        f"Include specific feedback about what was improved and what still needs work. "
        f"Increment the iteration counter by 1."
    )
    .consumes(
        EssayDraft,
        where=lambda d: d.quality_score < QUALITY_THRESHOLD and d.iteration < MAX_ITERATIONS,
    )
    .publishes(EssayDraft)
)


# ============================================================================
# STEP 3: Seed the Loop and Run
# ============================================================================

async def main():
    print("=" * 60)
    print("  Feedback Loop — Flock (Self-Consuming Pattern)")
    print("=" * 60)
    print()
    print(f"  Quality threshold: {QUALITY_THRESHOLD}/10")
    print(f"  Max iterations: {MAX_ITERATIONS}")
    print()

    # Seed with a low-quality initial draft
    initial = EssayDraft(
        topic="The future of AI agent orchestration",
        content="AI agents are cool. They do stuff. The end.",
        iteration=0,
        quality_score=2,
        feedback="Initial draft — needs significant improvement.",
    )

    print(f"  Initial draft (quality: {initial.quality_score}/10):")
    print(f"    \"{initial.content}\"")
    print()

    await flock.publish(initial)
    await flock.run_until_idle()

    # Retrieve ALL drafts to see the evolution
    all_drafts = await flock.store.get_by_type(EssayDraft)

    # Sort by iteration
    all_drafts.sort(key=lambda d: d.iteration)

    print("  ITERATION HISTORY:")
    print("  " + "-" * 40)
    for draft in all_drafts:
        print(f"  Iteration {draft.iteration} (quality: {draft.quality_score}/10)")
        # Show first 150 chars of content
        preview = draft.content[:150].replace("\n", " ")
        print(f"    Content: \"{preview}...\"")
        if draft.feedback:
            print(f"    Feedback: {draft.feedback[:100]}...")
        print()

    final = all_drafts[-1]
    if final.quality_score >= QUALITY_THRESHOLD:
        print(f"  Loop ended: quality target reached ({final.quality_score}/{QUALITY_THRESHOLD})")
    elif final.iteration >= MAX_ITERATIONS:
        print(f"  Loop ended: max iterations reached ({final.iteration}/{MAX_ITERATIONS})")

    print()
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())


# ============================================================================
# YOUR TURN!
# ============================================================================
#
# EXPERIMENT 1: Change the Threshold
# Set QUALITY_THRESHOLD = 9. Does the loop run more iterations?
# Set MAX_ITERATIONS = 5. How many iterations does it take to reach 9?
#
# EXPERIMENT 2: Watch the Improvement
# Compare the initial draft to the final. How much did it improve?
# Are the quality_score self-assessments accurate?
#
# EXPERIMENT 3: Different Starting Quality
# Start with quality_score=6 (already decent). Fewer iterations?
#
# COMPARE: The AF version uses explicit graph cycles with state.
# Which approach makes the loop logic more obvious?
# ============================================================================
