"""
Module 00 - Smoke Test

Run this FIRST to verify your environment is set up correctly.
It checks: Python version, imports, API key, and makes one LLM call
through each framework.

Usage:
    uv run 00-introduction/smoke_test.py
"""

import asyncio
import os
import sys


def check(label: str, passed: bool, detail: str = "") -> bool:
    status = "PASS" if passed else "FAIL"
    msg = f"  [{status}] {label}"
    if detail:
        msg += f" — {detail}"
    print(msg)
    return passed


async def main():
    print("=" * 60)
    print("  Smoke Test — Environment Verification")
    print("=" * 60)
    print()

    all_passed = True

    # ── 1. Python version ──────────────────────────────────────
    v = sys.version_info
    all_passed &= check(
        "Python version",
        v.major == 3 and v.minor >= 12,
        f"{v.major}.{v.minor}.{v.micro}",
    )

    # ── 2. Flock import ────────────────────────────────────────
    try:
        from flock import Flock  # noqa: F401
        from flock.registry import flock_type  # noqa: F401
        all_passed &= check("Flock import", True)
    except ImportError as e:
        all_passed &= check("Flock import", False, str(e))

    # ── 3. Agent Framework import ──────────────────────────────
    try:
        from agent_framework.openai import OpenAIResponsesClient  # noqa: F401
        from agent_framework import WorkflowBuilder  # noqa: F401
        all_passed &= check("Agent Framework import", True)
    except ImportError as e:
        all_passed &= check("Agent Framework import", False, str(e))

    # ── 4. Environment variables ───────────────────────────────
    from dotenv import load_dotenv
    load_dotenv()

    api_key = os.environ.get("OPENAI_API_KEY", "")
    has_key = bool(api_key) and api_key != "sk-your-key-here"
    all_passed &= check(
        "OPENAI_API_KEY set",
        has_key,
        "found" if has_key else "missing or placeholder — edit your .env file",
    )

    default_model = os.environ.get("DEFAULT_MODEL", "")
    all_passed &= check(
        "DEFAULT_MODEL set",
        bool(default_model),
        default_model or "missing — Flock will use its built-in default",
    )

    responses_model = os.environ.get("OPENAI_RESPONSES_MODEL_ID", "")
    all_passed &= check(
        "OPENAI_RESPONSES_MODEL_ID set",
        bool(responses_model),
        responses_model or "missing — Agent Framework will use its built-in default",
    )

    # ── 5. Live LLM calls (only if key is set) ────────────────
    if has_key:
        print()
        print("  Running live API checks (one call per framework)...")
        print()

        # Flock quick call
        try:
            from pydantic import BaseModel, Field
            from flock import Flock
            from flock.registry import flock_type

            @flock_type
            class Ping(BaseModel):
                message: str = Field(description="A short message")

            @flock_type
            class Pong(BaseModel):
                reply: str = Field(description="A short reply")

            f = Flock()
            f.agent("responder").description(
                "Reply with exactly one word: 'pong'"
            ).consumes(Ping).publishes(Pong)

            await f.publish(Ping(message="ping"))
            await f.run_until_idle()
            pongs = await f.store.get_by_type(Pong)
            all_passed &= check("Flock LLM call", len(pongs) > 0, pongs[0].reply if pongs else "no response")
        except Exception as e:
            all_passed &= check("Flock LLM call", False, str(e)[:80])

        # Agent Framework quick call
        try:
            from agent_framework.openai import OpenAIResponsesClient
            client = OpenAIResponsesClient()
            agent = client.as_agent(name="ping", instructions="Reply with exactly one word: pong")
            result = await agent.run("ping")
            text = str(result).strip()
            all_passed &= check("Agent Framework LLM call", bool(text), text[:40])
        except Exception as e:
            all_passed &= check("Agent Framework LLM call", False, str(e)[:80])
    else:
        print()
        print("  Skipping live API checks (no API key configured)")

    # ── Summary ────────────────────────────────────────────────
    print()
    print("=" * 60)
    if all_passed:
        print("  All checks passed! You're ready for Module 01.")
    else:
        print("  Some checks failed. Fix the issues above, then re-run:")
        print("    uv run 00-introduction/smoke_test.py")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
