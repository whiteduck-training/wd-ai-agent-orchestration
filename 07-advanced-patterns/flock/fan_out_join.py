"""
Module 07 - Fan-Out + AND-Gate Join (Flock)

LEARNING OBJECTIVE:
Implement a fan-out pattern where one artifact triggers multiple agents,
then an AND-gate agent waits for ALL results before producing a summary.

KEY CONCEPTS:
- Multiple agents consuming the same type = automatic fan-out
- .consumes(TypeA, TypeB, TypeC) = AND-gate (waits for all)
- The join agent only triggers when ALL required types are present
- No explicit fan-out/fan-in wiring needed
"""

import asyncio

from pydantic import BaseModel, Field

from flock import Flock
from flock.registry import flock_type


# ============================================================================
# STEP 1: Define Types for a Code Review Pipeline
# ============================================================================
# One CodeSubmission triggers three reviewers in parallel.
# The merge agent waits for ALL three reviews before producing a decision.
# ============================================================================

@flock_type
class CodeSubmission(BaseModel):
    """A code submission to review."""
    author: str = Field(description="Author name")
    language: str = Field(description="Programming language")
    description: str = Field(description="What the code does")
    code_snippet: str = Field(description="The code to review")


@flock_type
class SecurityReview(BaseModel):
    """Security-focused code review."""
    vulnerabilities: list[str] = Field(description="Security issues found")
    risk_level: str = Field(description="Overall risk: low, medium, high, critical")
    approved: bool = Field(description="Whether the code passes security review")


@flock_type
class PerformanceReview(BaseModel):
    """Performance-focused code review."""
    issues: list[str] = Field(description="Performance issues found")
    complexity: str = Field(description="Algorithmic complexity assessment")
    approved: bool = Field(description="Whether the code passes performance review")


@flock_type
class StyleReview(BaseModel):
    """Code style and best practices review."""
    suggestions: list[str] = Field(description="Style improvement suggestions")
    readability_score: int = Field(description="Readability score 1-10")
    approved: bool = Field(description="Whether the code passes style review")


@flock_type
class MergeDecision(BaseModel):
    """Final merge decision based on all reviews."""
    approved: bool = Field(description="Whether to approve the merge")
    summary: str = Field(description="Summary of all reviews")
    required_changes: list[str] = Field(description="Changes required before merge")


# ============================================================================
# STEP 2: Create Parallel Reviewers + AND-Gate Merger
# ============================================================================
# Three reviewers all consume CodeSubmission → fan-out (automatic)
# The merger consumes ALL THREE review types → AND-gate (waits for all)
# ============================================================================

flock = Flock()

security_reviewer = (
    flock.agent("security_reviewer")
    .description(
        "A security expert who reviews code for vulnerabilities, injection risks, "
        "authentication issues, and data exposure. Be specific about findings."
    )
    .consumes(CodeSubmission)
    .publishes(SecurityReview)
)

performance_reviewer = (
    flock.agent("performance_reviewer")
    .description(
        "A performance engineer who reviews code for efficiency, memory usage, "
        "algorithmic complexity, and scalability issues. Be specific about findings."
    )
    .consumes(CodeSubmission)
    .publishes(PerformanceReview)
)

style_reviewer = (
    flock.agent("style_reviewer")
    .description(
        "A code quality expert who reviews for readability, naming conventions, "
        "documentation, and adherence to best practices. Rate readability 1-10."
    )
    .consumes(CodeSubmission)
    .publishes(StyleReview)
)

# AND-gate: waits for ALL three review types
merge_agent = (
    flock.agent("merge_decision")
    .description(
        "A tech lead who makes the final merge decision based on all three reviews. "
        "Approve only if ALL reviewers approve. List any required changes."
    )
    .consumes(SecurityReview, PerformanceReview, StyleReview)
    .publishes(MergeDecision)
)


# ============================================================================
# STEP 3: Run the Pipeline
# ============================================================================

async def main():
    print("=" * 60)
    print("  Fan-Out + AND-Gate Join — Flock")
    print("=" * 60)
    print()

    submission = CodeSubmission(
        author="developer",
        language="Python",
        description="User authentication endpoint",
        code_snippet="""
def login(username, password):
    query = f"SELECT * FROM users WHERE name='{username}' AND pass='{password}'"
    user = db.execute(query)
    if user:
        token = base64.b64encode(f"{username}:{time.time()}".encode())
        return {"token": token, "user": user}
    return {"error": "Invalid credentials"}
""".strip(),
    )

    print(f"  Reviewing code from: {submission.author}")
    print(f"  Language: {submission.language}")
    print(f"  Description: {submission.description}")
    print()
    print("  Three reviewers running in PARALLEL...")
    print("  Merge agent waits for ALL THREE (AND-gate)...")
    print()

    await flock.publish(submission)
    await flock.run_until_idle()

    # Check individual reviews
    sec = await flock.store.get_by_type(SecurityReview)
    perf = await flock.store.get_by_type(PerformanceReview)
    style = await flock.store.get_by_type(StyleReview)

    if sec:
        print(f"  SECURITY: risk={sec[0].risk_level}, approved={sec[0].approved}")
    if perf:
        print(f"  PERFORMANCE: complexity={perf[0].complexity}, approved={perf[0].approved}")
    if style:
        print(f"  STYLE: readability={style[0].readability_score}/10, approved={style[0].approved}")
    print()

    # Check merge decision
    decisions = await flock.store.get_by_type(MergeDecision)
    if decisions:
        d = decisions[0]
        status = "APPROVED" if d.approved else "CHANGES REQUESTED"
        print(f"  MERGE DECISION: {status}")
        print(f"  Summary: {d.summary}")
        if d.required_changes:
            print("  Required changes:")
            for change in d.required_changes:
                print(f"    - {change}")

    print()
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())


# ============================================================================
# YOUR TURN!
# ============================================================================
#
# EXPERIMENT 1: What Happens Without the AND-Gate?
# Change merge_agent to .consumes(SecurityReview) only.
# It will trigger after JUST the security review. Is that what you want?
#
# EXPERIMENT 2: Add a Fourth Reviewer
# Create a TestCoverageReview type and a "test_reviewer" agent.
# Add TestCoverageReview to the merger's .consumes() list.
# Does the AND-gate wait for all four?
#
# COMPARE: The AF version uses explicit fan-out + fan-in edges.
# Which approach is cleaner for this pattern?
# ============================================================================
