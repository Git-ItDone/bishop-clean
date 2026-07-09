# Bernie Clean Roadmap

Deadline target: Monday, July 13, 2026.

## Phase 1 - Foundation

- [x] Clone V1 reference repo
- [x] Baseline V1 inventory
- [x] Baseline V1 tests
- [x] Create clean package skeleton
- [x] Create CLI shell
- [x] Create tool registry
- [x] Create read-only file tool
- [x] Add initial tests
- [ ] Commit initial clean rebuild

## Phase 2 - Safety and Tools

- [ ] Port/rewrite pure safety classifier
- [ ] Add audit sink
- [ ] Add approval policy
- [ ] Add write file tool with plan-only support
- [ ] Add edit file tool with line-range safety
- [ ] Add shell tool with timeout, output truncation, and approval gates
- [ ] Add search tools
- [ ] Add git tools

## Phase 3 - Agent Runtime

- [ ] Define model-client protocol
- [ ] Add Ollama/OpenAI-compatible client
- [ ] Normalize tool calls from structured and fallback text output
- [ ] Build agent loop against protocols
- [ ] Add max-turn and malformed-tool-call handling
- [ ] Add final response contract

## Phase 4 - Context and Memory

- [ ] Add project detection
- [ ] Add context collection
- [ ] Add identity/system prompt assembly
- [ ] Add session save/load
- [ ] Add workspace memory summaries
- [ ] Add compaction after core loop works

## Phase 5 - Runtime Surfaces

- [ ] Polish CLI one-shot mode
- [ ] Add REPL/resume mode
- [ ] Add ACP adapter
- [ ] Add local host API only after CLI is stable

## Phase 6 - Hardening

- [ ] Full test suite
- [ ] Local smoke test against Ollama
- [ ] Package install test
- [ ] GitHub repo publish
- [ ] Documentation cleanup

