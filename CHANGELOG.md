# Changelog

All notable changes to `palveron-openai-agents` will be documented in this file.

This project follows [Semantic Versioning](https://semver.org/).

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
