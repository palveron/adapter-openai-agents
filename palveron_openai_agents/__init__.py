"""
palveron-openai-agents — PALVERON Governance for the OpenAI Agents SDK
================================================================

Middleware hooks for the official OpenAI Agents framework.
Checks agent inputs, outputs, and tool calls against PALVERON policies.

Usage::

    from palveron_openai_agents import palveron_input_guardrail, palveron_output_guardrail
    from agents import Agent

    agent = Agent(
        name="assistant",
        instructions="You are a helpful assistant.",
        input_guardrails=[palveron_input_guardrail(api_key="pv_live_xxx")],
        output_guardrails=[palveron_output_guardrail(api_key="pv_live_xxx")],
    )
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from palveron import Palveron, VerifyRequest, PalveronError

__version__ = "0.1.0"
__all__ = [
    "palveron_input_guardrail",
    "palveron_output_guardrail",
    "PalveronGuardrailResult",
]

logger = logging.getLogger("palveron_openai_agents")


class PalveronGuardrailResult:
    """Result of a PALVERON governance check for OpenAI Agents."""

    def __init__(
        self,
        allowed: bool,
        decision: str,
        reason: str,
        trace_id: str,
        output: Optional[str] = None,
    ):
        self.allowed = allowed
        self.decision = decision
        self.reason = reason
        self.trace_id = trace_id
        self.output = output

    def __repr__(self) -> str:
        return f"PalveronGuardrailResult(decision={self.decision!r}, trace_id={self.trace_id!r})"


def palveron_input_guardrail(
    api_key: str,
    *,
    base_url: str = "https://gateway.palveron.com",
    fail_open: bool = False,
    metadata: Optional[dict[str, Any]] = None,
):
    """
    Create a PALVERON input guardrail for OpenAI Agents.

    Checks the user's input before the agent processes it.
    Raises ``GuardrailTripwireTriggered`` if PALVERON blocks the input.

    Example::

        from agents import Agent
        from palveron_openai_agents import palveron_input_guardrail

        agent = Agent(
            name="assistant",
            input_guardrails=[palveron_input_guardrail(api_key="pv_live_xxx")],
        )
    """
    client = Palveron(api_key=api_key, base_url=base_url)
    base_meta = {**(metadata or {}), "source": "openai-agents", "event": "input_guardrail"}

    async def _guardrail(ctx: Any, agent: Any, input_data: Any) -> Optional[Any]:
        text = _extract_text(input_data)
        if not text:
            return None

        try:
            result = client.verify(VerifyRequest(prompt=text, metadata=base_meta))

            if result.is_blocked:
                logger.warning(
                    "🚫 PALVERON BLOCKED input — %s (trace: %s)", result.reason, result.trace_id
                )
                # Import here to avoid hard dependency on specific agents SDK version
                try:
                    from agents import GuardrailTripwireTriggered

                    raise GuardrailTripwireTriggered(
                        f"Input blocked by PALVERON: {result.reason} (trace: {result.trace_id})"
                    )
                except ImportError:
                    raise RuntimeError(
                        f"Input blocked by PALVERON: {result.reason} (trace: {result.trace_id})"
                    )

            logger.debug("✅ PALVERON ALLOWED input (trace: %s)", result.trace_id)
            return None  # Allow — no tripwire

        except (PalveronError, Exception) as e:
            if isinstance(e, (RuntimeError,)):
                raise
            if fail_open:
                logger.warning("⚠️ PALVERON input check error, fail-open: %s", e)
                return None
            raise RuntimeError(f"PALVERON governance error (fail-closed): {e}")

    _guardrail.__name__ = "palveron_input_guardrail"
    return _guardrail


def palveron_output_guardrail(
    api_key: str,
    *,
    base_url: str = "https://gateway.palveron.com",
    fail_open: bool = False,
    metadata: Optional[dict[str, Any]] = None,
):
    """
    Create a PALVERON output guardrail for OpenAI Agents.

    Checks the agent's output before it's returned to the user.

    Example::

        from agents import Agent
        from palveron_openai_agents import palveron_output_guardrail

        agent = Agent(
            name="assistant",
            output_guardrails=[palveron_output_guardrail(api_key="pv_live_xxx")],
        )
    """
    client = Palveron(api_key=api_key, base_url=base_url)
    base_meta = {**(metadata or {}), "source": "openai-agents", "event": "output_guardrail"}

    async def _guardrail(ctx: Any, agent: Any, output_data: Any) -> Optional[Any]:
        text = _extract_text(output_data)
        if not text:
            return None

        try:
            result = client.verify(VerifyRequest(prompt=text, metadata=base_meta))

            if result.is_blocked:
                logger.warning(
                    "🚫 PALVERON BLOCKED output — %s (trace: %s)", result.reason, result.trace_id
                )
                try:
                    from agents import GuardrailTripwireTriggered

                    raise GuardrailTripwireTriggered(
                        f"Output blocked by PALVERON: {result.reason} (trace: {result.trace_id})"
                    )
                except ImportError:
                    raise RuntimeError(
                        f"Output blocked by PALVERON: {result.reason} (trace: {result.trace_id})"
                    )

            logger.debug("✅ PALVERON ALLOWED output (trace: %s)", result.trace_id)
            return None

        except (PalveronError, Exception) as e:
            if isinstance(e, (RuntimeError,)):
                raise
            if fail_open:
                logger.warning("⚠️ PALVERON output check error, fail-open: %s", e)
                return None
            raise RuntimeError(f"PALVERON governance error (fail-closed): {e}")

    _guardrail.__name__ = "palveron_output_guardrail"
    return _guardrail


def _extract_text(data: Any) -> str:
    """Extract text from various OpenAI Agents data types."""
    if isinstance(data, str):
        return data
    if hasattr(data, "text"):
        return str(data.text)
    if hasattr(data, "content"):
        return str(data.content)
    if isinstance(data, dict):
        for key in ("text", "content", "input", "output", "message"):
            if key in data:
                return str(data[key])
    if isinstance(data, list):
        parts = []
        for item in data:
            t = _extract_text(item)
            if t:
                parts.append(t)
        return "\n".join(parts)
    return str(data) if data else ""
