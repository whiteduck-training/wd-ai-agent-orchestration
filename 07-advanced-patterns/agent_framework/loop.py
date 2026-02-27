"""
Module 07 - Iterative Loop (Agent Framework)

LEARNING OBJECTIVE:
Implement an iterative refinement loop using graph cycles and
workflow state to track progress.

KEY CONCEPTS:
- Graph cycles create loops (edge from downstream back to upstream)
- WorkflowContext.set_state() / get_state() track iteration state
- Conditional edges break the loop when quality is sufficient
- Explicit loop control via state + conditions
"""

import asyncio
import os

from dotenv import load_dotenv
from typing_extensions import Never

from agent_framework import (
    AgentExecutor,
    AgentExecutorRequest,
    AgentExecutorResponse,
    Case,
    Default,
    Executor,
    Message,
    WorkflowBuilder,
    WorkflowContext,
    executor,
    handler,
)
from agent_framework.azure import AzureOpenAIResponsesClient
from agent_framework.openai import OpenAIResponsesClient


# ============================================================================
# STEP 1: Define State and Constants
# ============================================================================

load_dotenv()


def _clean_env(name: str) -> str:
    return os.getenv(name, "").strip().strip('"').strip("'")


def create_client():
    azure_api_key = _clean_env("AZURE_API_KEY")
    azure_api_base = _clean_env("AZURE_API_BASE")
    azure_api_version = _clean_env("AZURE_API_VERSION") or None
    default_model = _clean_env("DEFAULT_MODEL")

    if azure_api_key and azure_api_base and default_model.startswith("azure/"):
        deployment_name = default_model.split("/", 1)[1]
        return AzureOpenAIResponsesClient(
            api_key=azure_api_key,
            endpoint=azure_api_base,
            api_version=azure_api_version,
            deployment_name=deployment_name,
        )

    return OpenAIResponsesClient()

QUALITY_THRESHOLD = 7
MAX_ITERATIONS = 3


# ============================================================================
# STEP 2: Create Executor Nodes
# ============================================================================

@executor(id="seed")
async def seed_draft(topic: str, ctx: WorkflowContext[AgentExecutorRequest]) -> None:
    """Create the initial prompt for the writer agent."""
    ctx.set_state("iteration", 0)
    ctx.set_state("topic", topic)
    await ctx.send_message(
        AgentExecutorRequest(
            messages=[Message("user", text=(
                f"Write a short essay (2-3 paragraphs) about: {topic}\n"
                f"This is iteration 0. Write a first draft.\n"
                f"End your response with: QUALITY: [1-10]"
            ))],
            should_respond=True,
        )
    )


@executor(id="evaluate")
async def evaluate_draft(
    response: AgentExecutorResponse, ctx: WorkflowContext[str]
) -> None:
    """Parse the quality score and decide whether to continue."""
    text = response.agent_response.text or ""
    iteration = ctx.get_state("iteration") or 0

    # Parse quality score from response
    quality = 5  # default
    for line in reversed(text.split("\n")):
        if "QUALITY:" in line.upper():
            try:
                score_str = line.split(":")[-1].strip()
                quality = int(score_str.split("/")[0].strip())
            except (ValueError, IndexError):
                pass
            break

    ctx.set_state("iteration", iteration + 1)
    ctx.set_state("quality", quality)
    ctx.set_state("last_draft", text)

    # Send quality info for routing
    await ctx.send_message(f"quality={quality},iteration={iteration + 1}")


@executor(id="refine_prompt")
async def refine_prompt(
    eval_result: str, ctx: WorkflowContext[AgentExecutorRequest]
) -> None:
    """Create a refinement prompt for the next iteration."""
    iteration = ctx.get_state("iteration") or 1
    last_draft = ctx.get_state("last_draft") or ""
    topic = ctx.get_state("topic") or "unknown"

    await ctx.send_message(
        AgentExecutorRequest(
            messages=[Message("user", text=(
                f"Improve this essay about '{topic}'. This is iteration {iteration}.\n"
                f"Previous draft:\n{last_draft}\n\n"
                f"Make it better: improve clarity, add depth, strengthen arguments.\n"
                f"Target quality: {QUALITY_THRESHOLD}/10.\n"
                f"End your response with: QUALITY: [1-10]"
            ))],
            should_respond=True,
        )
    )


@executor(id="finalize")
async def finalize(eval_result: str, ctx: WorkflowContext[Never, str]) -> None:
    """Output the final draft."""
    quality = ctx.get_state("quality") or 0
    iteration = ctx.get_state("iteration") or 0
    draft = ctx.get_state("last_draft") or ""

    reason = "quality target reached" if quality >= QUALITY_THRESHOLD else "max iterations reached"
    await ctx.yield_output(
        f"FINAL RESULT (iteration {iteration}, quality {quality}/10, {reason})\n"
        f"{'=' * 40}\n{draft}"
    )


# ============================================================================
# STEP 3: Build the Loop Graph
# ============================================================================
# Graph:
#   seed → writer → evaluate → SWITCH:
#     needs_refinement → refine_prompt → writer (LOOP BACK)
#     done             → finalize (EXIT)
# ============================================================================

client = create_client()

writer_agent = AgentExecutor(
    client.as_agent(
        name="writer",
        instructions=(
            "You are an essay writer. Write or improve essays based on the prompt. "
            "Always end with QUALITY: [score] where score is 1-10 (be honest)."
        ),
    )
)


def needs_refinement(message) -> bool:
    """Check if the draft needs more work."""
    if not isinstance(message, str):
        return False
    parts = dict(p.split("=") for p in message.split(",") if "=" in p)
    quality = int(parts.get("quality", "0"))
    iteration = int(parts.get("iteration", "0"))
    return quality < QUALITY_THRESHOLD and iteration < MAX_ITERATIONS


def is_done(message) -> bool:
    """Check if the draft is good enough or we've hit max iterations."""
    return not needs_refinement(message)


workflow = (
    WorkflowBuilder(start_executor=seed_draft)
    .add_edge(seed_draft, writer_agent)
    .add_edge(writer_agent, evaluate_draft)
    .add_switch_case_edge_group(
        evaluate_draft,
        [
            Case(condition=needs_refinement, target=refine_prompt),
            Default(target=finalize),
        ],
    )
    .add_edge(refine_prompt, writer_agent)  # LOOP BACK
    .build()
)


# ============================================================================
# STEP 4: Run the Loop
# ============================================================================

async def main():
    print("=" * 60)
    print("  Iterative Loop — Agent Framework (Graph Cycle)")
    print("=" * 60)
    print()
    print(f"  Quality threshold: {QUALITY_THRESHOLD}/10")
    print(f"  Max iterations: {MAX_ITERATIONS}")
    print()

    events = await workflow.run("The future of AI agent orchestration")
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
# EXPERIMENT 1: Change the Threshold
# Set QUALITY_THRESHOLD = 9 and MAX_ITERATIONS = 5.
# How many iterations does it take?
#
# EXPERIMENT 2: Add Streaming
# Use workflow.run(topic, stream=True) to watch the loop in real-time.
# Can you see each iteration's output as it happens?
#
# EXPERIMENT 3: State Inspection
# Add print statements in evaluate_draft to see the state at each iteration.
# How does the quality score change?
#
# COMPARE: The Flock version achieves this with a self-consuming agent:
# - Agent consumes and publishes the SAME type
# - where= predicate controls the loop
# Which approach makes the loop logic more explicit?
# ============================================================================
