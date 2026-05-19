# Changelog

All notable changes to `palveron-openai-agents` will be documented in this file.

This project follows [Semantic Versioning](https://semver.org/).

## [1.1.0] — 2026-05-19

### Changed
- Requires `palveron-sdk>=1.1.0` for the gateway's Sprint-87 HTTP semantics
  (200/202/403/429 surface as governance decisions, not exceptions).
- `palveron_input_guardrail` and `palveron_output_guardrail` now trip the
  guardrail tripwire (or raise `RuntimeError` when the `agents` package
  isn't installed) for `PENDING_APPROVAL` and `RATE_LIMITED` in addition
  to `BLOCKED`. Previously these would never reach the adapter because
  the SDK raised; the new SDK returns them and the adapter surfaces
  them explicitly so the agent doesn't silently consume disallowed I/O.
- Tripwire logic factored into `_trip_if_non_pass()` so input and output
  guardrails stay in sync.
- Fixed `__version__` lagging behind `pyproject.toml` (was `"0.1.0"`);
  both now resolve to `1.1.0`.

## [1.0.0] — 2026-05-17

### Added
- Initial public release of `palveron-openai-agents` on PyPI
- Drop-in middleware that wires the Palveron gateway into the
  official OpenAI Agents SDK
- Per-agent, per-tool-call audit trail with trace IDs returned by the
  gateway
- Automatic blocking of disallowed tool invocations, with the policy
  reason surfaced as an OpenAI Agents tool error
- Compatible with the synchronous `Palveron` and the async `AsyncPalveron`
  clients from `palveron-sdk`
- Full type hints (PEP 561 compliant via `py.typed`)
