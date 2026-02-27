"""
Module 05 - Tools and Functions (Flock)

LEARNING OBJECTIVE:
Give agents the ability to call external functions (tools) using Flock's
tool integration via litellm function calling.

KEY CONCEPTS:
- Define Python functions as tools for agents
- Agents decide when and how to call tools based on their instructions
- Tools provide real-world data that agents incorporate into their output
- Flock uses litellm's function calling protocol
"""

import asyncio
import random

from pydantic import BaseModel, Field

from flock import Flock
from flock.registry import flock_type


# ============================================================================
# STEP 1: Define Tool Functions
# ============================================================================
# Tools are regular Python functions that agents can call.
# They provide capabilities beyond the LLM's training data:
# real-time weather, currency conversion, database lookups, etc.
#
# In Flock, tools are passed to agents and invoked via litellm's
# function calling protocol.
# ============================================================================

def get_weather(city: str) -> str:
    """Get the current weather for a city.

    Args:
        city: The city name to get weather for.

    Returns:
        A string describing the weather conditions.
    """
    # Simulated weather data (in production, call a real API)
    conditions = ["sunny", "partly cloudy", "overcast", "rainy", "stormy"]
    temps = {"sunny": 28, "partly cloudy": 24, "overcast": 20, "rainy": 16, "stormy": 14}
    condition = random.choice(conditions)
    temp = temps[condition] + random.randint(-3, 3)
    return f"{city}: {condition}, {temp}°C ({int(temp * 9/5 + 32)}°F)"


def convert_currency(amount: float, from_currency: str, to_currency: str) -> str:
    """Convert an amount between currencies.

    Args:
        amount: The amount to convert.
        from_currency: Source currency code (e.g., USD, EUR).
        to_currency: Target currency code (e.g., EUR, JPY).

    Returns:
        A string with the conversion result.
    """
    # Simulated exchange rates (in production, call a real API)
    rates = {
        ("USD", "EUR"): 0.92, ("EUR", "USD"): 1.09,
        ("USD", "JPY"): 149.50, ("JPY", "USD"): 0.0067,
        ("USD", "GBP"): 0.79, ("GBP", "USD"): 1.27,
        ("EUR", "GBP"): 0.86, ("GBP", "EUR"): 1.16,
        ("EUR", "JPY"): 162.50, ("JPY", "EUR"): 0.0062,
    }
    pair = (from_currency.upper(), to_currency.upper())
    if pair[0] == pair[1]:
        return f"{amount:.2f} {pair[0]} = {amount:.2f} {pair[1]}"
    rate = rates.get(pair, 1.0)
    converted = amount * rate
    return f"{amount:.2f} {from_currency.upper()} = {converted:.2f} {to_currency.upper()} (rate: {rate})"


def get_attractions(city: str) -> str:
    """Get top attractions for a city.

    Args:
        city: The city name to look up attractions for.

    Returns:
        A string listing top attractions.
    """
    # Simulated attraction data
    attractions = {
        "tokyo": "1. Senso-ji Temple 2. Shibuya Crossing 3. Meiji Shrine 4. Tokyo Tower 5. Tsukiji Outer Market",
        "paris": "1. Eiffel Tower 2. Louvre Museum 3. Notre-Dame 4. Montmartre 5. Champs-Elysees",
        "london": "1. Big Ben 2. Tower of London 3. British Museum 4. Buckingham Palace 5. Hyde Park",
    }
    city_lower = city.lower()
    for key, value in attractions.items():
        if key in city_lower:
            return f"Top attractions in {city}: {value}"
    return f"Top attractions in {city}: City center, local markets, historical district, main park, cultural museum"


# ============================================================================
# STEP 2: Define Types and Create Agent with Tools
# ============================================================================
# The travel planner agent receives a TravelRequest and uses tools
# to gather real-time information before producing a TravelPlan.
# ============================================================================

@flock_type
class TravelRequest(BaseModel):
    """A request to plan a trip."""
    destination: str = Field(description="Destination city")
    duration_days: int = Field(description="Trip duration in days")
    budget_usd: float = Field(description="Budget in USD")
    interests: list[str] = Field(description="Travel interests (e.g., culture, food, nature)")


@flock_type
class TravelPlan(BaseModel):
    """A complete travel plan."""
    destination: str = Field(description="Destination city")
    weather_summary: str = Field(description="Weather conditions at the destination")
    budget_local: str = Field(description="Budget converted to local currency")
    daily_itinerary: list[str] = Field(description="Day-by-day itinerary")
    top_attractions: list[str] = Field(description="Must-visit attractions")
    travel_tips: list[str] = Field(description="Practical travel tips")


flock = Flock()

travel_planner = (
    flock.agent("travel_planner")
    .description(
        "A travel planning expert. Use the available tools to:\n"
        "1. Check the weather at the destination\n"
        "2. Convert the budget to local currency\n"
        "3. Look up top attractions\n"
        "Then create a comprehensive travel plan based on the real data."
    )
    .consumes(TravelRequest)
    .publishes(TravelPlan)
    .tools(get_weather, convert_currency, get_attractions)
)


# ============================================================================
# STEP 3: Run the Agent with Tools
# ============================================================================

async def main():
    print("=" * 60)
    print("  Tools & Functions — Flock (litellm Function Calling)")
    print("=" * 60)
    print()

    request = TravelRequest(
        destination="Tokyo",
        duration_days=5,
        budget_usd=2000.0,
        interests=["culture", "food", "technology"],
    )

    print(f"  Destination: {request.destination}")
    print(f"  Duration: {request.duration_days} days")
    print(f"  Budget: ${request.budget_usd}")
    print(f"  Interests: {', '.join(request.interests)}")
    print()
    print("  Planning trip (agent will call tools for real-time data)...")
    print()

    await flock.publish(request)
    await flock.run_until_idle()

    plans = await flock.store.get_by_type(TravelPlan)
    if plans:
        plan = plans[0]
        print(f"  Destination: {plan.destination}")
        print(f"  Weather: {plan.weather_summary}")
        print(f"  Budget (local): {plan.budget_local}")
        print()
        print("  Itinerary:")
        for day in plan.daily_itinerary:
            print(f"    {day}")
        print()
        print("  Top Attractions:")
        for attraction in plan.top_attractions:
            print(f"    - {attraction}")
        print()
        print("  Travel Tips:")
        for tip in plan.travel_tips:
            print(f"    - {tip}")
    else:
        print("  No plan generated. Check your .env configuration.")

    print()
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())


# ============================================================================
# YOUR TURN!
# ============================================================================
#
# EXPERIMENT 1: Add a New Tool
# Create a get_flights(origin, destination, date) function that
# returns simulated flight prices. Add it to the agent's .tools().
#
# EXPERIMENT 2: Different Destinations
# Try "Paris", "London", or a city not in our simulated data.
# How does the agent handle missing tool data?
#
# EXPERIMENT 3: Tool-Only Agent
# Create an agent that ONLY uses tools (no creative output).
# For example: a "fact_checker" that verifies claims using tools.
#
# COMPARE: After running the Agent Framework version, consider:
# - Flock: tools passed via .tools() method
# - AF: tools passed via @tool decorator + tools= parameter
# - Which approach gives you better control over tool approval?
# ============================================================================
