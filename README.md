# vexis-openai-agents

VEXIS AI Governance for the **OpenAI Agents SDK** — input and output guardrails with audit trails.

[![PyPI](https://img.shields.io/pypi/v/vexis-openai-agents.svg?style=flat-square)](https://pypi.org/project/vexis-openai-agents/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg?style=flat-square)](https://opensource.org/licenses/Apache-2.0)

## Installation

```bash
pip install vexis-openai-agents
```

## Quick Start

```python
from agents import Agent
from vexis_openai_agents import vexis_input_guardrail, vexis_output_guardrail

agent = Agent(
    name="assistant",
    instructions="You are a helpful assistant.",
    input_guardrails=[vexis_input_guardrail(api_key="gp_live_xxx")],
    output_guardrails=[vexis_output_guardrail(api_key="gp_live_xxx")],
)

# Inputs with PII → blocked before the agent sees them
# Outputs with secrets → blocked before the user sees them
```

## How It Works

| Guardrail | When | What happens on BLOCKED |
|-----------|------|------------------------|
| `vexis_input_guardrail` | Before agent processes input | Raises `GuardrailTripwireTriggered` |
| `vexis_output_guardrail` | Before output reaches user | Raises `GuardrailTripwireTriggered` |

Every check creates an immutable trace in your VEXIS project for audit and compliance.

## Configuration

```python
guardrail = vexis_input_guardrail(
    api_key="gp_live_xxx",
    base_url="https://gateway.internal.corp:8080",  # On-prem
    fail_open=False,          # Block on gateway errors (default)
    metadata={"team": "ml"},  # Extra metadata on traces
)
```

## Links

- [Documentation](https://docs.vexis.io/integrations/openai-agents)
- [VEXIS Dashboard](https://app.vexis.io)
- [GitHub](https://github.com/disruptivetrends/vexis-openai-agents)

## License

[Apache 2.0](./LICENSE)
