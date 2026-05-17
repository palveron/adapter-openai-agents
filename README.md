# palveron-openai-agents

PALVERON AI Governance for the **OpenAI Agents SDK** — input and output guardrails with audit trails.

[![PyPI](https://img.shields.io/pypi/v/palveron-openai-agents.svg?style=flat-square)](https://pypi.org/project/palveron-openai-agents/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg?style=flat-square)](https://opensource.org/licenses/Apache-2.0)

## Installation

```bash
pip install palveron-openai-agents
```

## Quick Start

```python
from agents import Agent
from palveron_openai_agents import palveron_input_guardrail, palveron_output_guardrail

agent = Agent(
    name="assistant",
    instructions="You are a helpful assistant.",
    input_guardrails=[palveron_input_guardrail(api_key="pv_live_xxx")],
    output_guardrails=[palveron_output_guardrail(api_key="pv_live_xxx")],
)

# Inputs with PII → blocked before the agent sees them
# Outputs with secrets → blocked before the user sees them
```

## How It Works

| Guardrail | When | What happens on BLOCKED |
|-----------|------|------------------------|
| `palveron_input_guardrail` | Before agent processes input | Raises `GuardrailTripwireTriggered` |
| `palveron_output_guardrail` | Before output reaches user | Raises `GuardrailTripwireTriggered` |

Every check creates an immutable trace in your PALVERON project for audit and compliance.

## Configuration

```python
guardrail = palveron_input_guardrail(
    api_key="pv_live_xxx",
    base_url="https://gateway.internal.corp:8080",  # On-prem
    fail_open=False,          # Block on gateway errors (default)
    metadata={"team": "ml"},  # Extra metadata on traces
)
```

## Links

- [Documentation](https://docs.palveron.com/integrations/openai-agents)
- [PALVERON Dashboard](https://app.palveron.com)
- [GitHub](https://github.com/palveron/palveron-openai-agents)

## License

[Apache 2.0](./LICENSE)
