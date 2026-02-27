"""
Module 00 - Smoke Test

Run this FIRST to verify your environment is set up correctly.
It checks: Python version, imports, provider credentials, and makes one LLM call
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


def clean_env(name: str) -> str:
    """Read env var and normalize quoted values."""
    return os.environ.get(name, "").strip().strip('"').strip("'")


def has_real_value(name: str) -> bool:
    """Check env var exists and is not a known placeholder."""
    value = clean_env(name)
    placeholders = {
        "",
        "sk-your-key-here",
        "your-azure-key-here",
        "your-key-here",
        "https://your-resource.cognitiveservices.azure.com/",
    }
    return value not in placeholders


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
        from agent_framework.azure import AzureOpenAIResponsesClient  # noqa: F401
        from agent_framework import WorkflowBuilder  # noqa: F401
        all_passed &= check("Agent Framework import", True)
    except ImportError as e:
        all_passed &= check("Agent Framework import", False, str(e))

    # ── 4. Environment variables ───────────────────────────────
    from dotenv import load_dotenv
    load_dotenv()

    default_model = clean_env("DEFAULT_MODEL")
    using_azure_model = default_model.startswith("azure/")
    has_openai_key = has_real_value("OPENAI_API_KEY")
    has_azure_key = has_real_value("AZURE_API_KEY")
    has_azure_base = has_real_value("AZURE_API_BASE")
    has_azure_version = bool(clean_env("AZURE_API_VERSION"))

    # Flock credential checks
    if using_azure_model:
        all_passed &= check(
            "Flock Azure creds",
            has_azure_key and has_azure_base,
            "AZURE_API_KEY + AZURE_API_BASE required for DEFAULT_MODEL=azure/...",
        )
    else:
        all_passed &= check(
            "Flock OpenAI key",
            has_openai_key,
            "OPENAI_API_KEY required when DEFAULT_MODEL is not azure/...",
        )

    # Agent Framework provider detection
    af_uses_azure = has_azure_key and has_azure_base and using_azure_model
    af_mode = "azure" if af_uses_azure else "openai"
    all_passed &= check(
        "Agent Framework provider",
        True,
        af_mode,
    )

    if has_azure_key and has_azure_base and not using_azure_model and not has_openai_key:
        all_passed &= check(
            "Provider configuration",
            False,
            "Azure creds detected but DEFAULT_MODEL is not azure/<deployment> and OPENAI_API_KEY is missing",
        )

    if af_uses_azure:
        all_passed &= check(
            "AZURE_API_KEY set",
            has_azure_key,
            "found" if has_azure_key else "missing or placeholder",
        )
        all_passed &= check(
            "AZURE_API_BASE set",
            has_azure_base,
            "found" if has_azure_base else "missing or placeholder",
        )
        all_passed &= check(
            "AZURE_API_VERSION set (optional)",
            True,
            clean_env("AZURE_API_VERSION") if has_azure_version else "not set — Agent Framework will use its default",
        )
        all_passed &= check(
            "DEFAULT_MODEL deployment",
            using_azure_model and bool(default_model.split("/", 1)[1] if "/" in default_model else ""),
            default_model or "missing",
        )
    else:
        all_passed &= check(
            "OPENAI_API_KEY set",
            has_openai_key,
            "found" if has_openai_key else "missing or placeholder — edit your .env file",
        )
        responses_model = clean_env("OPENAI_RESPONSES_MODEL_ID")
        all_passed &= check(
            "OPENAI_RESPONSES_MODEL_ID set (optional)",
            True,
            responses_model or "not set — Agent Framework will use its built-in default",
        )

    all_passed &= check(
        "DEFAULT_MODEL set",
        bool(default_model),
        default_model or "missing — Flock will use its built-in default",
    )

    # ── 5. Live LLM calls ──────────────────────────────────────
    flock_ready = (using_azure_model and has_azure_key and has_azure_base) or (not using_azure_model and has_openai_key)
    af_ready = (af_uses_azure and has_azure_key and has_azure_base) or (not af_uses_azure and has_openai_key)

    if flock_ready or af_ready:
        print()
        print("  Running live API checks (one call per framework)...")
        print()

        # Flock quick call
        if flock_ready:
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
                all_passed &= check("Flock LLM call", False, str(e)[:120])
        else:
            all_passed &= check("Flock LLM call", False, "credentials not configured for selected DEFAULT_MODEL")

        # Agent Framework quick call
        if af_ready:
            try:
                if af_uses_azure:
                    from agent_framework.azure import AzureOpenAIResponsesClient

                    deployment_name = default_model.split("/", 1)[1]
                    client = AzureOpenAIResponsesClient(
                        api_key=clean_env("AZURE_API_KEY"),
                        endpoint=clean_env("AZURE_API_BASE"),
                        api_version=clean_env("AZURE_API_VERSION") or None,
                        deployment_name=deployment_name,
                    )
                else:
                    from agent_framework.openai import OpenAIResponsesClient

                    client = OpenAIResponsesClient()

                agent = client.as_agent(name="ping", instructions="Reply with exactly one word: pong")
                result = await agent.run("ping")
                text = str(result).strip()
                all_passed &= check("Agent Framework LLM call", bool(text), text[:40])
            except Exception as e:
                all_passed &= check("Agent Framework LLM call", False, str(e)[:120])
        else:
            all_passed &= check("Agent Framework LLM call", False, "credentials not configured for selected provider")
    else:
        print()
        print("  Skipping live API checks (no valid credentials configured)")

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
