# Custom Agent Profiles

Read this reference when installing, changing, or diagnosing Team Mode profiles. Normal dispatch does not need profile inspection.

## Profiles

Copy the templates from the repository's `agents/` directory into `~/.codex/agents/` for personal use or `<project>/.codex/agents/` for one project. Keep unrelated local profiles and compare same-named files before replacing them.

| Role | Model | Effort | Tier | Purpose |
| --- | --- | --- | --- | --- |
| `Explorer` | `gpt-6-luna` | `medium` | `fast` | Locate primary files in a large codebase when the parent requests it. |
| `Executor` | `gpt-6-luna` | `xhigh` | inherited | Complete a bounded implementation. |
| `Reviewer` | `gpt-6-sol` | `high` | inherited | Review a stable result and save a Markdown report when useful. |
| `ExpertAdvisor` | selected per consultation | selected per consultation | inherited | Investigate a complex decision or carry out assigned modeling or automation. |

`ExpertAdvisor.toml` deliberately omits `model` and `model_reasoning_effort`. Choose them at spawn time. Current Codex applies a custom profile's fixed model and effort *after* resolving explicit spawn values, so a fixed profile wins over a conflicting spawn request. Other models and roles may be configured; Team Mode does not impose a global model allowlist. See the [Codex subagent documentation](https://learn.chatgpt.com/docs/agent-configuration/subagents#custom-agents).

## Optional Default Sentinel

Codex includes a built-in general-purpose `default` agent. The repository also provides an optional `default.toml` sentinel, using `gpt-6-luna` at `low` effort. Installing it under `~/.codex/agents/` overrides the built-in default for **all** local tasks and makes an omitted or `default` dispatch return `DISPATCH BLOCKED`. This catches routing mistakes but still creates a child and consumes usage; it is not a security boundary. Team Mode works without it and still asks the parent to name the intended role explicitly.

To disable an installed personal sentinel without deleting it:

```bash
mkdir -p ~/.codex/agents-disabled
mv ~/.codex/agents/default.toml ~/.codex/agents-disabled/default.toml
```

Move it back to `~/.codex/agents/default.toml` to restore it. Open a new task or restart Codex after either change. A project-scoped sentinel can be moved into a corresponding project `agents-disabled/` directory.

## Load And Verify

1. Parse the installed TOML files and check `name`, `description`, `developer_instructions`, model, and effort where configured.
2. Open a new Codex task or restart if role changes do not appear in the current task. The current task's role schema may have been loaded before the edit.
3. Check that `spawn_agent` exposes the intended `agent_type` and, for `ExpertAdvisor`, explicit `model` and `reasoning_effort`. Do not route to a generic child when the intended custom role is absent.
4. For a real delegated task, compare the child trace's role, model, and effort with the request. A file's existence and the child self-report are not runtime proof.

## Explorer Fast Tier

Fast is a service tier, separate from model and reasoning effort. `Explorer.toml` requests it with `service_tier = "fast"`, even when its parent uses Standard. The other profiles inherit their parent's tier. Codex applies this field to the child configuration when Fast mode is enabled. The current `spawn_agent` interface has no per-dispatch service-tier argument. Check the child's effective tier before relying on it because availability depends on the model and host. GPT-6 Fast consumes 2.5 times the Standard credits where available. See the [Speed guide](https://learn.chatgpt.com/docs/agent-configuration/speed), [custom-agent configuration](https://learn.chatgpt.com/docs/agent-configuration/subagents#custom-agents), and [role override implementation](https://github.com/openai/codex/blob/main/codex-rs/core/src/agent/role.rs).

If the runtime does not expose the necessary dispatch controls or ignores a requested role, use the main agent while diagnosing the issue. Restart or update Codex, then check a new task. Do not reuse a version-specific workaround without matching evidence.
