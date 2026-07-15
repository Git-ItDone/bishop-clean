# Bishop: portfolio case study

## The problem

AI assistants are easy to demo and hard to trust when they can read files, write files, run shell commands, and carry out multi-step tasks. The hard part is not getting a model to produce text. The hard part is making the execution path understandable: what can act, where can it act, when does it need approval, and what evidence remains after it runs?

## The build

Bishop is a local-first coding-agent runtime designed around those questions. It turns a natural-language task into an agent loop that can request structured tools, then routes each request through a registry and applicable workspace, safety, approval, and audit boundaries. The shell boundary is deliberately called out as limited: commands run with the workspace as their current directory, but are not sandboxed.

The project is intentionally small enough to inspect. Each concern has a boundary and a test suite:

- **Tool registry:** named tools, explicit JSON schemas, argument parsing, and dispatch.
- **Workspace tools:** read, write, edit, file discovery, and text search are confined to an explicit working directory; shell processes start in that directory but are not sandboxed.
- **Safety policy:** classifies actions as safe, caution, dangerous, or blocked without performing the action itself.
- **Approval policy:** separates authorization from the classifier; writes and all shell commands need explicit run-level opt-in.
- **Audit sink:** appends structured JSONL evidence for write, edit, and command outcomes and fails open so an audit-file problem does not crash the task.
- **Model transport:** uses Ollama’s OpenAI-compatible endpoint and normalizes structured tool calls for the agent loop.

## Why the design matters

The public-interest version of this problem is not “put an agent everywhere.” It is “make a tool safe enough for people to understand, supervise, and maintain.” A staff member should be able to see what the system did, when it needed a human decision, and where the record lives. A future owner should be able to change one boundary without reverse-engineering an entire prototype.

That is why Bishop defaults to local execution, requires explicit opt-in for writes and every shell command, confines file and search operations to a designated workspace, blocks dangerous patterns, and records writes, edits, and commands in an audit trail. It does **not** claim to sandbox shell commands; its README makes that limit explicit.

## What I learned

The first version of an agent should not be expanded by adding more tools. It should be strengthened by reducing ambiguity:

1. Name the boundary between model output and real-world action.
2. Classify risk before execution.
3. Require meaningful approval rather than treating a safety label as approval.
4. Test the failure paths, not only the successful demo.
5. Document limits plainly so the next person knows what is real and what is still planned.

## Verification

The repository includes a 52-test suite that covers safety, approval behavior, file boundaries, shell limits, audit records, registry behavior, model-response parsing, and multi-turn agent execution. GitHub Actions runs the suite on every push and pull request.

## Honest status

Bishop is a working early-stage runtime, not a finished autonomous coding platform. Durable memory, Git-native tools, a REPL, ACP integration, and a host API are future phases. The project demonstrates how I approach AI-enabled work: start with a useful narrow workflow, make assumptions and risk visible, verify behavior, and leave a clean handoff path.
