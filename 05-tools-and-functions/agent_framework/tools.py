"""
Module 05 - Tools and Functions (Agent Framework)

LEARNING OBJECTIVE:
Give agents the ability to call external functions using the @tool decorator
and understand tool approval modes.

KEY CONCEPTS:
- @tool decorator wraps Python functions as agent-callable tools
- approval_mode="never_require" auto-approves tool calls
- Tools use Annotated types with Field descriptions for the LLM
- Tools are passed to as_agent() via the tools= parameter
"""

import asyncio
import os
import random
from typing import Annotated

from dotenv import load_dotenv
from pydantic import Field

from agent_framework import tool
from agent_framework.azure import AzureOpenAIResponsesClient
from agent_framework.openai import OpenAIResponsesClient


# ============================================================================
# STEP 1: Define Tools with @tool Decorator
# ============================================================================
# The @tool decorator wraps functions so the Agent Framework can:
# - Generate a JSON schema for the LLM to understand parameters
# - Automatically call the function when the LLM requests it
# - Return the result back to the LLM for incorporation
#
# approval_mode="never_require" means the tool runs without user approval.
# In production, you might use "always_require" for sensitive operations.
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


@tool(approval_mode="never_require")
def get_weather(
    city: Annotated[str, Field(description="The city name to get weather for")],
) -> str:
    """Get the current weather for a city."""
    conditions = ["sunny", "partly cloudy", "overcast", "rainy", "stormy"]
    temps = {"sunny": 28, "partly cloudy": 24, "overcast": 20, "rainy": 16, "stormy": 14}
    condition = random.choice(conditions)
    temp = temps[condition] + random.randint(-3, 3)
    return f"{city}: {condition}, {temp}°C ({int(temp * 9/5 + 32)}°F)"


@tool(approval_mode="never_require")
def convert_currency(
    amount: Annotated[float, Field(description="The amount to convert")],
    from_currency: Annotated[str, Field(description="Source currency code (e.g., USD, EUR)")],
    to_currency: Annotated[str, Field(description="Target currency code (e.g., EUR, JPY)")],
) -> str:
    """Convert an amount between currencies."""
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


@tool(approval_mode="never_require")
def get_attractions(
    city: Annotated[str, Field(description="The city name to look up attractions for")],
) -> str:
    """Get top attractions for a city."""
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
# STEP 2: Create Agent with Tools
# ============================================================================
# Pass tools to as_agent() — the LLM decides when to call them.
# The agent's instructions should mention the available tools
# so the LLM knows to use them.
# ============================================================================

client = create_client()

travel_agent = client.as_agent(
    name="travel_planner",
    instructions=(
        "You are a travel planning expert. You have access to tools for:\n"
        "- get_weather: Check weather at a destination\n"
        "- convert_currency: Convert budget to local currency\n"
        "- get_attractions: Find top attractions\n\n"
        "When planning a trip:\n"
        "1. Check the weather at the destination\n"
        "2. Convert the budget to local currency\n"
        "3. Look up attractions\n"
        "4. Create a day-by-day itinerary using the real data from tools\n\n"
        "Always use the tools to get real data before making recommendations."
    ),
    tools=[get_weather, convert_currency, get_attractions],
)


# ============================================================================
# STEP 3: Run the Agent
# ============================================================================
# The agent will automatically call tools during its response generation.
# You can see tool calls in the streaming output.
# ============================================================================

async def main():
    print("=" * 60)
    print("  Tools & Functions — Agent Framework (@tool Decorator)")
    print("=" * 60)
    print()

    request = (
        "Plan a 5-day trip to Tokyo.\n"
        "Budget: $2000 USD\n"
        "Interests: culture, food, technology\n"
        "Please check the weather, convert my budget to JPY, and suggest attractions."
    )

    print("  Destination: Tokyo")
    print("  Duration: 5 days")
    print("  Budget: $2000 USD")
    print("  Interests: culture, food, technology")
    print()
    print("  Planning trip (agent will call tools for real-time data)...")
    print()

    # Non-streaming to see the full result
    result = await travel_agent.run(request)

    print("  " + "-" * 40)
    for line in str(result).split("\n"):
        print(f"  {line}")
    print("  " + "-" * 40)

    print()
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())


# ============================================================================
# YOUR TURN!
# ============================================================================
#
# EXPERIMENT 1: Add a Flight Search Tool
# Create a @tool function for get_flights(origin, destination).
# Add it to the agent's tools list.
#
# EXPERIMENT 2: Approval Modes
# Change get_weather to approval_mode="always_require".
# What happens when the agent tries to call it?
# (Note: approval requires interactive mode — you'll see the behavior change)
#
# EXPERIMENT 3: Streaming with Tool Calls
# Use agent.run(request, stream=True) and observe the chunks.
# Can you see when tool calls happen vs when text is generated?
#
# EXPERIMENT 4: Tool-Only Response
# Ask the agent: "What's the weather in Paris and London?"
# The response should be entirely based on tool data.
#
# COMPARE: After running the Flock version, consider:
# - Flock: tools via .tools() method on the agent
# - AF: tools via @tool decorator + tools= parameter
# - AF has approval_mode for tool-level control. Flock doesn't.
# - Which approach gives you more granular control?
# ============================================================================
