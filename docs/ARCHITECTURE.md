# Bishop Clean Architecture

Bishop Clean is a local-first coding-agent runtime rebuilt from Bernie V1 concepts with explicit boundaries.

## Boundary Map

### CLI Layer

Owns argument parsing and user-facing commands only.

It should not know how tools execute, how approvals work, or how model calls are made.

### Runtime Layer

Owns task orchestration:

- Build runtime config
- Construct registry
- Construct model client
- Run agent loop
- Return final result

### Agent Loop

Owns conversation state and turn progression:

- System prompt construction
- User task injection
- Model call
- Tool-call dispatch
- Tool-result append
- Completion detection
- Max-turn termination

The loop should depend on protocols/interfaces, not concrete Ollama, file, shell, or audit implementations.

### Model Client

Owns model transport:

- Ollama/OpenAI-compatible request/response handling
- Streaming/non-streaming text
- Tool-call normalization
- Provider errors

### Tool Registry

Owns tool metadata and dispatch:

- Tool names
- JSON schema
- Required argument validation
- String result normalization

It should not own safety policy, audit policy, or workspace path policy.

### Tool Implementations

Own concrete operations:

- Read files
- Write/edit files
- Run shell commands
- Search files
- Git operations
- Web fetch/search

Tools receive explicit service dependencies: workspace policy, approval policy, audit sink.

### Safety Policy

Pure classification only:

- SAFE
- CAUTION
- DANGEROUS
- BLOCKED

No execution. No prompts. No filesystem mutation.

### Approval Policy

Owns allow/deny decisions:

- Allow once
- Allow always
- Reject once
- Reject always

Approval memory is session-scoped and separate from classification.

### Audit Sink

Owns append-only logging:

- Tool name
- Risk tier
- Outcome
- Workspace
- Details

Audit failures must not crash normal execution.

### Memory/Session

Owns durable context:

- Completed task summaries
- Session messages
- Workspace-scoped memory

Storage backend should be replaceable.

## V1 Concepts Worth Keeping

- Local-first Ollama support
- OpenAI-compatible tool-call schema
- Tool registry pattern
- Workspace-confined file tools
- Safety tiers and path classification
- Approval policy with always/once decisions
- Audit JSONL logs
- Session persistence
- Project detection and context collection
- ACP/host surfaces, after core is clean

## V1 Patterns To Avoid

- Tool implementations doing too many policy jobs
- Tight coupling between CLI, registry, and concrete tools
- Brittle integration tests that depend on local model availability
- Runtime imports that make isolated unit testing hard
- Broad docs/spec sprawl without an execution source of truth

