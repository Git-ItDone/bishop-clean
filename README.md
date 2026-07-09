# Bernie Clean

Clean rebuild of the Bernie/BernAgent local coding-agent runtime.

`bernie-v1-reference` is treated as source material only. This project keeps the useful concepts while rebuilding the runtime with clear boundaries, testable services, and minimal coupling.

## Goals

- Local-first coding agent runtime
- Clean CLI and task runner
- Explicit tool registry and tool execution contracts
- Approval policy separate from tool implementation
- Audit logging separate from safety classification
- Memory/session storage with replaceable backends
- Model client abstraction with Ollama as the first implementation
- Tests for every boundary before expanding behavior

## Non-Goals

- Blindly copying V1 internals
- Shipping V1 spaghetti with a new name
- Adding cloud dependencies by default
- Hiding write/command risk from the user

## Deadline

Target functional rebuild by Monday, July 13, 2026.

