# Bishop Roadmap

## Current release posture

Bishop is a working, local-first **v0.1.0 runtime** with explicit tool, safety, approval, and audit boundaries. It is intentionally not presented as a finished autonomous platform. The next work should deepen core reliability before adding new surfaces.

## Phase 1 — Foundation

- [x] Clean package skeleton and CLI
- [x] Model-client protocol
- [x] Explicit tool registry and execution contracts
- [x] Workspace-confined read, write, edit, shell, and search tools
- [x] Tests for core boundaries

## Phase 2 — Safe local execution

- [x] Pure safety classifier
- [x] Approval policy separated from risk classification
- [x] CLI-level write and command confirmations
- [x] Persistent JSONL audit records
- [x] Timeout and output caps for shell execution
- [x] Structured and fallback JSON tool-call normalization
- [x] Invalid tool-argument rejection without crashing the agent loop

## Phase 3 — Verified delivery baseline

- [x] Full unit test suite
- [x] Local Ollama smoke test using `qwen2.5-coder:1.5b`
- [x] Built-wheel installation smoke test
- [x] GitHub Actions test workflow
- [x] Public README, architecture, portfolio case study, and license

## Next, in order

1. [ ] Improve live tool-use reliability across supported local models and add integration fixtures based on real provider responses.
2. [ ] Add Git-native tools with the existing safety/approval/audit contracts.
3. [ ] Add a final-response contract that reports completed work, evidence, and remaining risk.
4. [ ] Add durable session memory and workspace summaries only after the core loop is stable.
5. [ ] Add REPL/resume mode.
6. [ ] Consider ACP and a local host API only after the CLI is proven in repeated real tasks.

## Non-goals

- Hiding write or command risk from the user
- Claiming production autonomy before the runtime earns it
- Copying V1 internals wholesale
- Adding cloud dependencies by default
