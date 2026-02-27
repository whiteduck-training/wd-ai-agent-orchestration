"""
Module 04 - Conditional Routing (Agent Framework)

LEARNING OBJECTIVE:
Route messages to different agents based on conditions using
switch-case edge groups with Case and Default.

KEY CONCEPTS:
- add_switch_case_edge_group() creates conditional routing
- Case(condition=predicate, target=agent) routes when predicate is true
- Default(target=agent) handles unmatched cases
- Centralized routing — one decision point controls the path
"""

import asyncio
import os
from dataclasses import dataclass

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
# STEP 1: Define the Classification Result
# ============================================================================
# A classifier agent analyzes the ticket and produces a structured result.
# The switch-case routing then uses this result to choose the handler.
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


@dataclass
class ClassifiedTicket:
    """Result from the classifier — determines routing."""
    original_text: str
    priority: str       # critical, high, normal, low
    customer_tier: str   # enterprise, premium, standard
    route_to: str        # senior, experienced, standard


# ============================================================================
# STEP 2: Create Executor Nodes
# ============================================================================
# The classifier extracts priority info and determines the route.
# Handler agents process the ticket based on the route.
# ============================================================================

@executor(id="intake")
async def intake(ticket_text: str, ctx: WorkflowContext[AgentExecutorRequest]) -> None:
    """Receive a ticket and send it to the classifier agent."""
    await ctx.send_message(
        AgentExecutorRequest(
            messages=[Message("user", text=(
                f"Classify this support ticket. Respond with EXACTLY one line in this format:\n"
                f"ROUTE: [senior|experienced|standard]\n\n"
                f"Rules:\n"
                f"- critical priority OR enterprise tier → senior\n"
                f"- high priority (non-enterprise) → experienced\n"
                f"- normal or low priority (non-enterprise) → standard\n\n"
                f"Ticket:\n{ticket_text}"
            ))],
            should_respond=True,
        )
    )


@executor(id="parse_classification")
async def parse_classification(
    response: AgentExecutorResponse, ctx: WorkflowContext[ClassifiedTicket]
) -> None:
    """Parse the classifier's response into a structured routing decision."""
    text = response.agent_response.text or ""

    # Extract route from response
    route = "standard"  # default
    for line in text.split("\n"):
        if "ROUTE:" in line.upper():
            route_value = line.split(":")[-1].strip().lower()
            if route_value in ("senior", "experienced", "standard"):
                route = route_value
            break

    # Store original ticket for the handler
    original = ""
    for msg in response.agent_response.messages:
        if hasattr(msg, "text") and msg.text:
            original = msg.text
            break

    await ctx.send_message(ClassifiedTicket(
        original_text=original,
        priority="determined-by-classifier",
        customer_tier="determined-by-classifier",
        route_to=route,
    ))


@executor(id="senior_handler")
async def senior_handler(ticket: ClassifiedTicket, ctx: WorkflowContext[Never, str]) -> None:
    """Handle critical/enterprise tickets."""
    await ctx.yield_output(
        f"[SENIOR SUPPORT] Handling ticket with high urgency.\n"
        f"Ticket routed as: {ticket.route_to}"
    )


@executor(id="experienced_handler")
async def experienced_handler(ticket: ClassifiedTicket, ctx: WorkflowContext[Never, str]) -> None:
    """Handle high-priority tickets."""
    await ctx.yield_output(
        f"[EXPERIENCED SUPPORT] Handling high-priority ticket.\n"
        f"Ticket routed as: {ticket.route_to}"
    )


@executor(id="standard_handler")
async def standard_handler(ticket: ClassifiedTicket, ctx: WorkflowContext[Never, str]) -> None:
    """Handle normal/low-priority tickets."""
    await ctx.yield_output(
        f"[STANDARD SUPPORT] Handling routine ticket.\n"
        f"Ticket routed as: {ticket.route_to}"
    )


# ============================================================================
# STEP 3: Build the Workflow with Switch-Case Routing
# ============================================================================
# The graph:
#   intake → classifier_agent → parse_classification → SWITCH:
#     Case("senior")      → senior_handler
#     Case("experienced") → experienced_handler
#     Default             → standard_handler
#
# This is CENTRALIZED routing — one switch-case decides the path.
# ============================================================================

client = create_client()

classifier_agent = AgentExecutor(
    client.as_agent(
        name="classifier",
        instructions=(
            "You classify support tickets by priority and route them. "
            "Respond with exactly: ROUTE: [senior|experienced|standard]"
        ),
    )
)


def route_matches(expected: str):
    """Factory that creates a predicate for switch-case routing."""
    def condition(message) -> bool:
        return isinstance(message, ClassifiedTicket) and message.route_to == expected
    return condition


workflow = (
    WorkflowBuilder(start_executor=intake)
    .add_edge(intake, classifier_agent)
    .add_edge(classifier_agent, parse_classification)
    .add_switch_case_edge_group(
        parse_classification,
        [
            Case(condition=route_matches("senior"), target=senior_handler),
            Case(condition=route_matches("experienced"), target=experienced_handler),
            Default(target=standard_handler),
        ],
    )
    .build()
)


# ============================================================================
# STEP 4: Run with Different Tickets
# ============================================================================

async def main():
    print("=" * 60)
    print("  Conditional Routing — Agent Framework (Switch-Case)")
    print("=" * 60)
    print()

    tickets = [
        (
            "T-001: CRITICAL - Production system down\n"
            "Priority: critical | Customer: enterprise\n"
            "Our production API is returning 500 errors for all requests."
        ),
        (
            "T-002: HIGH - Slow dashboard\n"
            "Priority: high | Customer: premium\n"
            "The analytics dashboard takes 30+ seconds to load."
        ),
        (
            "T-003: NORMAL - Export question\n"
            "Priority: normal | Customer: standard\n"
            "How do I export my project data to CSV format?"
        ),
    ]

    for ticket in tickets:
        first_line = ticket.split("\n")[0]
        print(f"  Processing: {first_line}")

        events = await workflow.run(ticket)
        outputs = events.get_outputs()

        if outputs:
            print(f"  Result: {outputs[0]}")
        print()

    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())


# ============================================================================
# YOUR TURN!
# ============================================================================
#
# EXPERIMENT 1: Add a VIP Route
# Add a new Case for "vip" routing before the Default.
# Update the classifier instructions to identify VIP customers.
#
# EXPERIMENT 2: Replace Executor Handlers with AI Agents
# Instead of simple @executor handlers, use client.as_agent() with
# AgentExecutor for the handlers. Give each one different instructions.
#
# EXPERIMENT 3: Chained Routing
# Add a second switch-case after the senior_handler:
# If the ticket mentions "database", route to a DB specialist.
#
# COMPARE: After running the Flock version, consider:
# - Flock: decentralized routing (each agent filters its own input)
# - AF: centralized routing (one switch-case controls all paths)
# - Which is easier to add new routes to? Which is easier to audit?
# ============================================================================
