"""
Module 04 - Conditional Routing (Flock)

LEARNING OBJECTIVE:
Route artifacts to different agents based on conditions using Flock's
`where=` predicate on .consumes().

KEY CONCEPTS:
- where= takes a lambda that filters which artifacts an agent processes
- Multiple agents can consume the same type with different where= conditions
- The routing logic lives in the agent declaration, not in a central router
- This is decentralized routing — each agent decides what it handles
"""

import asyncio

from pydantic import BaseModel, Field

from flock import Flock
from flock.registry import flock_type


# ============================================================================
# STEP 1: Define Support Ticket Types
# ============================================================================
# A support ticket comes in with a priority level.
# Different agents handle different priorities.
# ============================================================================

@flock_type
class SupportTicket(BaseModel):
    """An incoming support ticket."""
    id: str = Field(description="Ticket ID")
    subject: str = Field(description="Ticket subject")
    description: str = Field(description="Full ticket description")
    priority: str = Field(description="Priority: critical, high, normal, low")
    customer_tier: str = Field(default="standard", description="Customer tier: enterprise, premium, standard")


@flock_type
class TicketResponse(BaseModel):
    """Response to a support ticket."""
    ticket_id: str = Field(description="Original ticket ID")
    response: str = Field(description="The response to the customer")
    escalated: bool = Field(description="Whether the ticket was escalated")
    handler: str = Field(description="Which agent handled this ticket")


# ============================================================================
# STEP 2: Create Agents with Conditional Routing
# ============================================================================
# The `where=` parameter on .consumes() filters artifacts.
# Only tickets matching the condition are processed by that agent.
#
# This is DECENTRALIZED routing — each agent declares its own filter.
# No central router needed.
# ============================================================================

flock = Flock()

# Critical tickets go to the senior support agent
senior_agent = (
    flock.agent("senior_support")
    .description(
        "A senior support specialist who handles critical and enterprise tickets. "
        "Provide detailed, thorough responses. Always acknowledge the urgency. "
        "Set escalated=true if the issue requires engineering involvement."
    )
    .consumes(
        SupportTicket,
        where=lambda t: t.priority == "critical" or t.customer_tier == "enterprise",
    )
    .publishes(TicketResponse)
)

# High priority tickets go to the experienced agent
experienced_agent = (
    flock.agent("experienced_support")
    .description(
        "An experienced support agent who handles high-priority tickets. "
        "Provide clear, actionable responses. Escalate if needed."
    )
    .consumes(
        SupportTicket,
        where=lambda t: t.priority == "high" and t.customer_tier != "enterprise",
    )
    .publishes(TicketResponse)
)

# Normal and low priority go to the standard agent
standard_agent = (
    flock.agent("standard_support")
    .description(
        "A friendly support agent who handles routine tickets. "
        "Provide helpful responses with links to documentation when appropriate."
    )
    .consumes(
        SupportTicket,
        where=lambda t: t.priority in ("normal", "low") and t.customer_tier != "enterprise",
    )
    .publishes(TicketResponse)
)


# ============================================================================
# STEP 3: Run with Different Tickets
# ============================================================================

async def main():
    print("=" * 60)
    print("  Conditional Routing — Flock (where= Predicates)")
    print("=" * 60)
    print()

    tickets = [
        SupportTicket(
            id="T-001",
            subject="Production system down",
            description="Our production API is returning 500 errors for all requests",
            priority="critical",
            customer_tier="enterprise",
        ),
        SupportTicket(
            id="T-002",
            subject="Slow dashboard loading",
            description="The analytics dashboard takes 30+ seconds to load",
            priority="high",
            customer_tier="premium",
        ),
        SupportTicket(
            id="T-003",
            subject="How to export data?",
            description="I'd like to export my project data to CSV format",
            priority="normal",
            customer_tier="standard",
        ),
    ]

    for ticket in tickets:
        print(f"  [{ticket.id}] {ticket.subject}")
        print(f"    Priority: {ticket.priority} | Tier: {ticket.customer_tier}")
        await flock.publish(ticket)

    print()
    print("  Processing all tickets (routing by priority + tier)...")
    print()

    await flock.run_until_idle()

    responses = await flock.store.get_by_type(TicketResponse)
    for resp in responses:
        print(f"  [{resp.ticket_id}] Handled by: {resp.handler}")
        print(f"    Escalated: {resp.escalated}")
        print(f"    Response: {resp.response[:120]}...")
        print()

    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())


# ============================================================================
# YOUR TURN!
# ============================================================================
#
# EXPERIMENT 1: Add a VIP Handler
# Create an agent that handles premium + critical tickets specifically.
# What happens if a ticket matches TWO agents' where= conditions?
#
# EXPERIMENT 2: Priority Escalation
# Create a new type EscalatedTicket and an "escalation_manager" agent.
# The senior_support agent should publish EscalatedTicket when escalated=true.
# This creates a secondary routing cascade!
#
# EXPERIMENT 3: Overlapping Conditions
# Remove the "enterprise" exclusion from experienced_agent's where=.
# Submit an enterprise + high ticket. Which agent(s) handle it?
#
# COMPARE: After running the Agent Framework version, consider:
# - Flock: each agent declares its own filter (decentralized)
# - AF: a central switch-case routes to specific agents (centralized)
# - Which is easier to maintain when routing rules change frequently?
# ============================================================================
