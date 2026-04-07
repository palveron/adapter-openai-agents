"""
vexis-openai-agents — VEXIS Governance for the OpenAI Agents SDK
================================================================

Middleware hooks for the official OpenAI Agents framework.
Checks agent inputs, outputs, and tool calls against VEXIS policies.

Usage::

    from vexis_openai_agents import vexis_input_guardrail, vexis_output_guardrail
    from agents import Agent

    agent = Agent(
        name="assistant",
        instructions="You are a helpful assistant.",
        input_guardrails=[vexis_input_guardrail(api_key="gp_live_xxx")],
        output_guardrails=[vexis_output_guardrail(api_key="gp_live_xxx")],
    )
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from vexis import Vexis, VerifyRequest, VexisError

__version__ = "0.1.0"
__all__ = [
    "vexis_input_guardrail",
    "vexis_output_guardrail",
    "VexisGuardrailResult",
]

logger = logging.getLogger("vexis_openai_agents")


class VexisGuardrailResult:
    """Result of a VEXIS governance check for OpenAI Agents."""

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
        return f"VexisGuardrailResult(decision={self.decision!r}, trace_id={self.trace_id!r})"


def vexis_input_guardrail(
    api_key: str,
    *,
    base_url: str = "https://gateway.vexis.io",
    fail_open: bool = False,
    metadata: Optional[dict[str, Any]] = None,
):
    """
    Create a VEXIS input guardrail for OpenAI Agents.

    Checks the user's input before the agent processes it.
    Raises ``GuardrailTripwireTriggered`` if VEXIS blocks the input.

    Example::

        from agents import Agent
        from vexis_openai_agents import vexis_input_guardrail

        agent = Agent(
            name="assistant",
            input_guardrails=[vexis_input_guardrail(api_key="gp_live_xxx")],
        )
    """
    client = Vexis(api_key=api_key, base_url=base_url)
    base_meta = {**(metadata or {}), "source": "openai-agents", "event": "input_guardrail"}

    async def _guardrail(ctx: Any, agent: Any, input_data: Any) -> Optional[Any]:
        text = _extract_text(input_data)
        if not text:
            return None

        try:
            result = client.verify(VerifyRequest(prompt=text, metadata=base_meta))

            if result.is_blocked:
                logger.warning(
                    "🚫 VEXIS BLOCKED input — %s (trace: %s)", result.reason, result.trace_id
                )
                # Import here to avoid hard dependency on specific agents SDK version
                try:
                    from agents import GuardrailTripwireTriggered

                    raise GuardrailTripwireTriggered(
                        f"Input blocked by VEXIS: {result.reason} (trace: {result.trace_id})"
                    )
                except ImportError:
                    raise RuntimeError(
                        f"Input blocked by VEXIS: {result.reason} (trace: {result.trace_id})"
                    )

            logger.debug("✅ VEXIS ALLOWED input (trace: %s)", result.trace_id)
            return None  # Allow — no tripwire

        except (VexisError, Exception) as e:
            if isinstance(e, (RuntimeError,)):
                raise
            if fail_open:
                logger.warning("⚠️ VEXIS input check error, fail-open: %s", e)
                return None
            raise RuntimeError(f"VEXIS governance error (fail-closed): {e}")

    _guardrail.__name__ = "vexis_input_guardrail"
    return _guardrail


def vexis_output_guardrail(
    api_key: str,
    *,
    base_url: str = "https://gateway.vexis.io",
    fail_open: bool = False,
    metadata: Optional[dict[str, Any]] = None,
):
    """
    Create a VEXIS output guardrail for OpenAI Agents.

    Checks the agent's output before it's returned to the user.

    Example::

        from agents import Agent
        from vexis_openai_agents import vexis_output_guardrail

        agent = Agent(
            name="assistant",
            output_guardrails=[vexis_output_guardrail(api_key="gp_live_xxx")],
        )
    """
    client = Vexis(api_key=api_key, base_url=base_url)
    base_meta = {**(metadata or {}), "source": "openai-agents", "event": "output_guardrail"}

    async def _guardrail(ctx: Any, agent: Any, output_data: Any) -> Optional[Any]:
        text = _extract_text(output_data)
        if not text:
            return None

        try:
            result = client.verify(VerifyRequest(prompt=text, metadata=base_meta))

            if result.is_blocked:
                logger.warning(
                    "🚫 VEXIS BLOCKED output — %s (trace: %s)", result.reason, result.trace_id
                )
                try:
                    from agents import GuardrailTripwireTriggered

                    raise GuardrailTripwireTriggered(
                        f"Output blocked by VEXIS: {result.reason} (trace: {result.trace_id})"
                    )
                except ImportError:
                    raise RuntimeError(
                        f"Output blocked by VEXIS: {result.reason} (trace: {result.trace_id})"
                    )

            logger.debug("✅ VEXIS ALLOWED output (trace: %s)", result.trace_id)
            return None

        except (VexisError, Exception) as e:
            if isinstance(e, (RuntimeError,)):
                raise
            if fail_open:
                logger.warning("⚠️ VEXIS output check error, fail-open: %s", e)
                return None
            raise RuntimeError(f"VEXIS governance error (fail-closed): {e}")

    _guardrail.__name__ = "vexis_output_guardrail"
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
