"""
Module 01 - Hello Agent (Agent Framework)

LEARNING OBJECTIVE:
Build your first Agent Framework agent and understand the direct-call pattern:
create a client, configure an agent with instructions, and run it.

KEY CONCEPTS:
- create_client() auto-selects Azure or OpenAI based on env vars
- client.as_agent() creates a configured agent
- agent.run() executes and returns a response
- Streaming with agent.run(stream=True) for real-time output
"""

import asyncio
import os

from dotenv import load_dotenv

from agent_framework.azure import AzureOpenAIResponsesClient
from agent_framework.openai import OpenAIResponsesClient


# ============================================================================
# STEP 1: Load Environment & Create Client
# ============================================================================
# Client selection reads from environment variables:
#   - Azure mode: AZURE_API_KEY + AZURE_API_BASE + DEFAULT_MODEL=azure/<deployment>
#   - OpenAI mode: OPENAI_API_KEY (+ optional OPENAI_RESPONSES_MODEL_ID)
#
# Unlike Flock's type-based approach, Agent Framework uses a client
# that you configure directly with instructions.
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


client = create_client()


# ============================================================================
# STEP 2: Create an Agent
# ============================================================================
# client.as_agent() creates an agent with:
#   - name: identifier for the agent
#   - instructions: system prompt that defines behavior
#
# Notice the difference from Flock: instead of typed artifacts, you
# provide natural language instructions. The "contract" is implicit
# in the instruction text, not explicit in type definitions.
# ============================================================================

poet_agent = client.as_agent(
    name="poet",
    instructions=(
        "You are a creative poet. When given a topic and style, write a beautiful poem. "
        "Format your response as:\n"
        "TITLE: [poem title]\n"
        "STYLE: [style used]\n"
        "---\n"
        "[the poem text]"
    ),
)


# ============================================================================
# STEP 3: Run the Agent
# ============================================================================
# agent.run(message) sends a message and returns the full response.
# agent.run(message, stream=True) returns chunks as they arrive.
#
# This is a direct call — no blackboard, no type matching, no automatic
# triggering. You explicitly call the agent and get a result.
# ============================================================================

async def main():
    print("=" * 60)
    print("  Hello Agent — Agent Framework (DAG Architecture)")
    print("=" * 60)
    print()

    topic = "the beauty of open source collaboration"
    style = "free verse"

    print(f"  Topic: {topic}")
    print(f"  Style: {style}")
    print()
    print("  Calling agent directly...")
    print()

    # Non-streaming: get the complete response at once
    result = await poet_agent.run(
        f"Write a {style} poem about: {topic}"
    )

    # result.text contains the full response
    print("  " + "-" * 40)
    for line in str(result).split("\n"):
        print(f"  {line}")
    print("  " + "-" * 40)

    print()
    print("  --- Now with streaming ---")
    print()

    # Streaming: get chunks as they're generated
    async for chunk in poet_agent.run(
        f"Write a short haiku about: {topic}",
        stream=True,
    ):
        if chunk.text:
            print(chunk.text, end="", flush=True)

    print()
    print()
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())


# ============================================================================
# YOUR TURN!
# ============================================================================
#
# EXPERIMENT 1: Change the Instructions
# Modify the agent's instructions to be more specific:
#   "You are a haiku master. Only write haikus (5-7-5 syllable pattern)."
# How does this compare to changing the Flock type's style field?
#
# EXPERIMENT 2: Streaming vs Non-Streaming
# Comment out the streaming section and only use non-streaming.
# When would you prefer one over the other?
#
# EXPERIMENT 3: Multiple Calls
# Call poet_agent.run() three times with different topics.
# Compare: In Flock, you published 3 artifacts. Here, you make 3 calls.
# Which approach feels more natural?
#
# EXPERIMENT 4: Structured Output
# Change the instructions to request JSON output and parse it.
# Compare this to Flock's typed Pydantic models.
#
# COMPARE: After running the Flock version, consider:
# - Flock uses type definitions; AF uses instruction strings. Trade-offs?
# - Flock triggers automatically; AF requires explicit calls. When is each better?
# - Where does each framework put the "contract" for agent behavior?
# ============================================================================
