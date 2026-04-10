# Changelog

All notable changes to Ephemeral are recorded here.

## 3.8.0

Released: 2026-04-09

### UI

- Rebuilt the Ink shell around a cleaner workspace, navigator sidebar, and prompt dock.
- Fixed inconsistent prompt focus and cursor behavior so typing always returns to the input surface.
- Added direct action switching from the empty composer so the shell feels live before any request runs.
- Reduced layout bloat and raised the stacked-layout fallback threshold to keep content inside the frame on smaller terminals.
- Improved rendered output formatting for status, help, ask/tool responses, and operational views.

### Setup and routing

- Optimized the Ink bridge so lightweight actions do not eagerly import heavy workflow modules.
- Added richer Ollama status details, including installed-model visibility and active-model availability.
- Updated setup to reuse already-installed Ollama models instead of assuming a fresh pull is required.
- Persisted `OLLAMA_MODEL` alongside the default provider and model to keep runtime routing aligned.

### Release hygiene

- Centralized version metadata in `ephemeral/version.py`.
- Bumped package, script, and verification references to `3.8.0`.
- Rewrote the README around the new `3.8.0` product story and command surface.
- Added setup regression tests in `tests/test_setup_agent.py`.
