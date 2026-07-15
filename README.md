# Bishop

[![CI](https://github.com/Git-ItDone/bishop-clean/actions/workflows/ci.yml/badge.svg)](https://github.com/Git-ItDone/bishop-clean/actions/workflows/ci.yml)

A local-first coding-agent runtime built to make tool use explicit, testable, and reviewable.

Bishop is not presented as a finished autonomous platform. It is a focused engineering build: a small agent loop, a typed tool registry, workspace-confined file and search tools, a separately gated shell tool, policy-based approval, durable JSONL audit records for writes, edits, and commands, and an Ollama-compatible model client. The point is judgment and maintainability—not pretending a demo is production infrastructure.

## Why it exists

Most AI-agent prototypes blur model behavior, filesystem access, command execution, and safety policy into one opaque loop. Bishop splits those concerns so each one can be inspected and tested independently:

- The model client only transports messages and normalizes structured tool calls.
- The agent loop only manages turns and conversation state.
- The registry owns tool schemas and dispatch.
- File and search tools own concrete operations inside a workspace; the shell tool starts processes with that workspace as its current directory but is not a sandbox.
- Safety classifies risk without executing anything.
- Approval decides whether a classified action may proceed.
- Audit records the outcome without being allowed to crash the run.

That separation is the project. It makes the system easier to explain to a non-technical stakeholder, safer to extend, and easier to hand off.

## What works today

- One-shot local CLI
- Ollama `/v1/chat/completions` client
- Structured OpenAI-style tool-call dispatch
- Workspace-confined read, write, edit, file-find, and text-search tools
- Shell commands that always require explicit CLI opt-in and begin with the workspace as their current directory
- Blocked protected paths and destructive command patterns
- JSONL audit trail for writes, edits, and commands at `<workspace>/.bishop/audit.jsonl`
- Test suite covering tool boundaries, safety classification, approval behavior, audit persistence, model transport, and the agent loop

## Deliberate limits

Bishop is an early, local runtime—not a completed product. It does not yet include durable session memory, a REPL, Git-native tools, an ACP adapter, a host API, or a live model benchmark. The roadmap is public because unfinished work should be named, not hidden.

## Quick start

Prerequisites: Python 3.11+ and a running [Ollama](https://ollama.com/) server.

```bash
git clone https://github.com/Git-ItDone/bishop-clean.git
cd bishop-clean
uv sync --group dev
ollama pull qwen2.5-coder:1.5b
```

Inspect available tools without calling a model:

```bash
uv run bishop --list-tools
```

Run against a local workspace. Writes and commands are denied unless explicitly enabled:

```bash
uv run bishop \
  --workspace ./example-workspace \
  --model qwen2.5-coder:1.5b \
  --confirm-writes \
  --confirm-commands \
  "Read the README, summarize the current structure, then propose the smallest safe improvement."
```

Writes, edits, and command decisions are recorded in `./example-workspace/.bishop/audit.jsonl`.

## Safety model

Bishop classifies a tool action before it runs:

| Tier | Behavior |
| --- | --- |
| `SAFE` | Read/search tools may proceed. Shell commands still require `--confirm-commands`. |
| `CAUTION` | Requires the matching explicit CLI opt-in. |
| `DANGEROUS` | Requires the matching explicit CLI opt-in. |
| `BLOCKED` | Refused unconditionally. |

`--confirm-writes` and `--confirm-commands` are run-level execution opt-ins: they authorize matching actions during that one Bishop run. They do not bypass blocked operations.

> **Warning:** Bishop is a local development experiment, not a sandbox or a security boundary. Shell commands run through the local shell with the workspace as their current directory and can reach resources outside that directory. Do not use it with sensitive data or untrusted tasks.

The conservative default is to refuse writes and all shell commands unless the operator explicitly enables them for that run.

## Architecture

```text
CLI
 └── Runtime configuration
      ├── Agent loop
      │    ├── Model-client protocol → Ollama client
      │    └── Tool registry → file / shell / search tools
      ├── Approval policy
      └── JSONL audit sink

Safety classification is a pure layer used by tools before execution.
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for boundary ownership and [docs/ROADMAP.md](docs/ROADMAP.md) for the deliberately sequenced build plan.

## Verification

```bash
uv run pytest -q
```

Current local verification: **51 passing tests**.

## Project context

Bishop was built by [Dejion Evans](https://www.linkedin.com/in/dejion-evans-21392b413/) as a portfolio project in practical AI workflow design: break a problem into explicit boundaries, make risk visible, test the important paths, and document what the next owner needs to know.

For the short application-oriented project narrative, see [docs/PORTFOLIO.md](docs/PORTFOLIO.md).

## License

MIT. See [LICENSE](LICENSE).
