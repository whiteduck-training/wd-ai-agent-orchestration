"""
Module 03 - Parallel Execution (Flock)

LEARNING OBJECTIVE:
Understand how Flock achieves automatic parallelism: when multiple agents
consume the same type, they ALL trigger simultaneously.

KEY CONCEPTS:
- Multiple agents consuming the same type = automatic parallelism
- No fan-out configuration needed — it's the default behavior
- AND-gate: .consumes(TypeA, TypeB) waits for BOTH before triggering
- All results land on the blackboard for collection
"""

import asyncio

from pydantic import BaseModel, Field

from flock import Flock
from flock.registry import flock_type


# ============================================================================
# STEP 1: Define Types for Product Analysis
# ============================================================================
# One input type (ProductInfo) consumed by THREE different analyst agents.
# Each produces a different report type.
#
# When ProductInfo is published, ALL THREE agents trigger in parallel.
# ============================================================================

@flock_type
class ProductInfo(BaseModel):
    """Information about a product to analyze."""
    name: str = Field(description="Product name")
    description: str = Field(description="Product description")
    price: float = Field(description="Price in USD")
    category: str = Field(description="Product category")


@flock_type
class MarketAnalysis(BaseModel):
    """Market positioning analysis."""
    positioning: str = Field(description="Market positioning assessment")
    competitors: list[str] = Field(description="Key competitors")
    opportunity_score: int = Field(description="Market opportunity score 1-10")


@flock_type
class TechnicalReview(BaseModel):
    """Technical feasibility review."""
    feasibility: str = Field(description="Technical feasibility assessment")
    risks: list[str] = Field(description="Technical risks identified")
    complexity_score: int = Field(description="Implementation complexity 1-10")


@flock_type
class CustomerInsight(BaseModel):
    """Customer perspective analysis."""
    target_persona: str = Field(description="Primary target customer persona")
    pain_points: list[str] = Field(description="Customer pain points addressed")
    appeal_score: int = Field(description="Customer appeal score 1-10")


# ============================================================================
# STEP 2: Create Three Parallel Agents
# ============================================================================
# All three agents consume ProductInfo — they will run in PARALLEL
# when a ProductInfo artifact appears on the blackboard.
#
# This is automatic. No fan-out configuration. No explicit parallelism.
# The blackboard pattern naturally supports concurrent execution.
# ============================================================================

flock = Flock()

market_analyst = (
    flock.agent("market_analyst")
    .description(
        "A market analyst who evaluates product positioning, identifies competitors, "
        "and assesses market opportunity. Be specific about competitor names and positioning."
    )
    .consumes(ProductInfo)
    .publishes(MarketAnalysis)
)

tech_reviewer = (
    flock.agent("tech_reviewer")
    .description(
        "A technical reviewer who assesses feasibility, identifies implementation risks, "
        "and evaluates complexity. Be specific about technical challenges."
    )
    .consumes(ProductInfo)
    .publishes(TechnicalReview)
)

customer_researcher = (
    flock.agent("customer_researcher")
    .description(
        "A customer researcher who identifies target personas, pain points, "
        "and customer appeal. Be specific about who would buy this and why."
    )
    .consumes(ProductInfo)
    .publishes(CustomerInsight)
)


# ============================================================================
# STEP 3: Run and Collect All Results
# ============================================================================
# One publish, one run_until_idle — three agents execute in parallel.
# All results are on the blackboard, retrievable by type.
# ============================================================================

async def main():
    print("=" * 60)
    print("  Parallel Execution — Flock (Automatic Parallelism)")
    print("=" * 60)
    print()

    product = ProductInfo(
        name="SmartGarden Pro",
        description="An AI-powered indoor garden that automatically adjusts light, water, and nutrients",
        price=299.99,
        category="Smart Home / IoT",
    )

    print(f"  Product: {product.name}")
    print(f"  Price: ${product.price}")
    print(f"  Category: {product.category}")
    print()
    print("  Publishing product info...")
    print("  (3 analysts will run in PARALLEL — same input, same time)")
    print()

    await flock.publish(product)
    await flock.run_until_idle()

    # Collect all results
    market = await flock.store.get_by_type(MarketAnalysis)
    tech = await flock.store.get_by_type(TechnicalReview)
    customer = await flock.store.get_by_type(CustomerInsight)

    if market:
        m = market[0]
        print(f"  MARKET ANALYSIS (opportunity: {m.opportunity_score}/10)")
        print(f"    Positioning: {m.positioning[:100]}...")
        print(f"    Competitors: {', '.join(m.competitors[:3])}")
        print()

    if tech:
        t = tech[0]
        print(f"  TECHNICAL REVIEW (complexity: {t.complexity_score}/10)")
        print(f"    Feasibility: {t.feasibility[:100]}...")
        print(f"    Risks: {', '.join(t.risks[:3])}")
        print()

    if customer:
        c = customer[0]
        print(f"  CUSTOMER INSIGHT (appeal: {c.appeal_score}/10)")
        print(f"    Target: {c.target_persona[:100]}...")
        print(f"    Pain points: {', '.join(c.pain_points[:3])}")
        print()

    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())


# ============================================================================
# YOUR TURN!
# ============================================================================
#
# EXPERIMENT 1: Add a Fourth Analyst
# Create a FinancialAnalysis type and a "financial_analyst" agent.
# It should also consume ProductInfo.
# Run again — does it automatically join the parallel execution?
#
# EXPERIMENT 2: AND-Gate (Aggregation)
# Create a Summary type and a "summarizer" agent that consumes ALL THREE
# report types: .consumes(MarketAnalysis, TechnicalReview, CustomerInsight)
# This agent will only trigger when ALL three reports exist.
#
# EXPERIMENT 3: Multiple Products
# Publish 2 ProductInfo artifacts. How many analyses are produced?
# (Hint: 3 agents × 2 products = ?)
#
# COMPARE: After running the Agent Framework version, consider:
# - Flock: 3 agents consume the same type → automatic parallelism
# - AF: explicit .add_fan_out_edges() required
# - Which approach is easier to add a 4th analyst to?
# ============================================================================
