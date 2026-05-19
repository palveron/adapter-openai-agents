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

__version__ = "1.1.0"
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
            _trip_if_non_pass(result, "input")
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
            _trip_if_non_pass(result, "output")
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


def _trip_if_non_pass(result: Any, surface: str) -> None:
    """Raise the OpenAI-Agents tripwire (or RuntimeError fallback) when
    the PALVERON decision is a non-pass outcome.

    Sprint 87 — the gateway emits three non-pass decisions for the
    verify path: ``BLOCKED`` (policy / capability / budget),
    ``PENDING_APPROVAL`` (queued for a human approver) and
    ``RATE_LIMITED`` (tier quota hit). All three halt the agent so it
    doesn't silently consume disallowed output; the caller branches on
    the tripwire's message / ``trace_id`` to do retry-vs-escalate.
    """
    decision_value = result.decision.value
    non_pass = {
        "BLOCKED": "🚫",
        "PENDING_APPROVAL": "⏳",
        "RATE_LIMITED": "🚦",
    }
    if decision_value not in non_pass:
        return

    logger.warning(
        "%s PALVERON %s %s — %s (trace: %s)",
        non_pass[decision_value], decision_value, surface, result.reason, result.trace_id,
    )
    message = (
        f"{surface.capitalize()} {decision_value.lower().replace('_', ' ')} by "
        f"PALVERON: {result.reason} (trace: {result.trace_id})"
    )
    try:
        from agents import GuardrailTripwireTriggered  # type: ignore[import-not-found]
        raise GuardrailTripwireTriggered(message)
    except ImportError:
        raise RuntimeError(message)


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
