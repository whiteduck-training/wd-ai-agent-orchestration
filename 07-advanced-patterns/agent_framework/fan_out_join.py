"""
Module 07 - Fan-Out + Fan-In Join (Agent Framework)

LEARNING OBJECTIVE:
Implement a fan-out/fan-in pattern where a dispatcher sends to multiple
agents in parallel and an aggregator waits for all results.

KEY CONCEPTS:
- add_fan_out_edges() broadcasts to multiple targets
- add_fan_in_edges() waits for ALL sources (synchronized barrier)
- The aggregator receives a list of all responses
- Explicit graph topology makes the pattern visible
"""

import asyncio
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
# STEP 1: Dispatcher — Sends Code to All Reviewers
# ============================================================================

load_dotenv()


class DispatchCode(Executor):
    """Receives code submission and dispatches to all reviewers."""

    @handler
    async def dispatch(self, code_text: str, ctx: WorkflowContext[AgentExecutorRequest]) -> None:
        await ctx.send_message(
            AgentExecutorRequest(
                messages=[Message("user", text=code_text)],
                should_respond=True,
            )
        )


# ============================================================================
# STEP 2: Aggregator — Collects All Reviews and Decides
# ============================================================================

class MergeReviews(Executor):
    """Collects all reviews and produces a merge decision."""

    @handler
    async def merge(
        self, reviews: list[AgentExecutorResponse], ctx: WorkflowContext[Never, str]
    ) -> None:
        report_parts = ["CODE REVIEW SUMMARY", "=" * 40, ""]

        for review in reviews:
            agent_name = review.executor_id or "unknown"
            text = review.agent_response.text or "(no response)"
            report_parts.append(f"[{agent_name.upper()}]")
            report_parts.append(text)
            report_parts.append("")

        report_parts.append("=" * 40)
        await ctx.yield_output("\n".join(report_parts))


# ============================================================================
# STEP 3: Create Review Agents and Build the Graph
# ============================================================================
# Graph:
#   dispatcher → [security, performance, style]  (fan-out)
#   [security, performance, style] → merger       (fan-in)
# ============================================================================

client = OpenAIResponsesClient()

security_agent = AgentExecutor(
    client.as_agent(
        name="security_reviewer",
        instructions=(
            "You are a security code reviewer. Analyze the code for:\n"
            "- SQL injection vulnerabilities\n"
            "- Authentication weaknesses\n"
            "- Data exposure risks\n"
            "Rate risk level (low/medium/high/critical) and state APPROVED or REJECTED."
        ),
    )
)

performance_agent = AgentExecutor(
    client.as_agent(
        name="performance_reviewer",
        instructions=(
            "You are a performance code reviewer. Analyze the code for:\n"
            "- Algorithmic complexity\n"
            "- Memory efficiency\n"
            "- Scalability concerns\n"
            "Rate complexity and state APPROVED or REJECTED."
        ),
    )
)

style_agent = AgentExecutor(
    client.as_agent(
        name="style_reviewer",
        instructions=(
            "You are a code style reviewer. Analyze the code for:\n"
            "- Readability and naming conventions\n"
            "- Documentation quality\n"
            "- Best practices adherence\n"
            "Rate readability (1-10) and state APPROVED or REJECTED."
        ),
    )
)

dispatcher = DispatchCode(id="dispatcher")
merger = MergeReviews(id="merger")

workflow = (
    WorkflowBuilder(start_executor=dispatcher)
    .add_fan_out_edges(dispatcher, [security_agent, performance_agent, style_agent])
    .add_fan_in_edges([security_agent, performance_agent, style_agent], merger)
    .build()
)


# ============================================================================
# STEP 4: Run the Review Pipeline
# ============================================================================

async def main():
    print("=" * 60)
    print("  Fan-Out + Fan-In Join — Agent Framework")
    print("=" * 60)
    print()

    code = """
Review this Python code:

```python
def login(username, password):
    query = f"SELECT * FROM users WHERE name='{username}' AND pass='{password}'"
    user = db.execute(query)
    if user:
        token = base64.b64encode(f"{username}:{time.time()}".encode())
        return {"token": token, "user": user}
    return {"error": "Invalid credentials"}
```
""".strip()

    print("  Submitting code for review...")
    print("  Graph: dispatcher → [security, perf, style] → merger")
    print()

    events = await workflow.run(code)
    outputs = events.get_outputs()

    if outputs:
        print(str(outputs[0]))
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
# EXPERIMENT 1: Add a Fourth Reviewer
# Create a test_coverage_agent and add it to fan-out AND fan-in.
# The merger now receives 4 reviews in its list.
#
# EXPERIMENT 2: Streaming
# Use workflow.run(code, stream=True) to see real-time progress.
# Which reviewer finishes first?
#
# COMPARE: The Flock version achieves the same with type declarations:
# - Three agents .consumes(CodeSubmission) = automatic fan-out
# - Merger .consumes(SecurityReview, PerformanceReview, StyleReview) = AND-gate
# Which approach is more explicit? Which is more concise?
# ============================================================================
