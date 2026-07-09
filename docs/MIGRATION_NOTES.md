# Migration Notes From Bernie V1

Source repository: `/Users/deposits/Desktop/Agent-Brain/projects/bernie-v1-reference`

The V1 repo is reference material only. Do not copy modules wholesale unless a later review explicitly marks a function as safe to port.

## Initial Inventory

- Package: `bernagent`
- Entrypoints: `bernagent`, `bernagent-acp`, `bernagent-host`
- Runtime surfaces: CLI, REPL, ACP adapter, FastAPI host
- Core modules: agent loop, Ollama/OpenAI client, tool registry, tools, approval, audit, safety, memory, session, compaction, project detection
- Tests: 402 total observed; 400 pass, 2 fail in model-swap integration

## Baseline Test Result

Command:

```bash
uv run --extra dev pytest -q
```

Result:

- 400 passed
- 2 failed
- 11 warnings

Failure summary:

- `tests/test_integration.py::test_context_survives_model_swap`
- `tests/test_integration.py::test_full_multi_model_workflow`

Reason: model-swap tests raise `ModelNotPulledError` for `qwen3-coder:30b`; the tests mock HTTPX but still depend on local model availability logic.

## Rebuild Decision

Start fresh under `bishop-clean` with small tested boundaries:

1. Tool registry
2. Workspace path policy
3. Read-only file tool
4. Safety classifier
5. Audit sink
6. Approval policy
7. Write/edit tools
8. Shell tool
9. Model client
10. Agent loop
11. CLI UX
12. Memory/session
13. ACP/host surfaces

## Current Clean Rebuild Status

- Package skeleton created.
- CLI entrypoint created.
- Tool registry created.
- Read file tool created.
- Initial tests pass.

