<p align="right">
  <strong>English</strong> · <a href="./README.zh-CN.md">简体中文</a>
</p>

<p align="center">
  <img src="./assets/readme/agent-map.webp" width="100%" alt="Team Mode routes evidence gathering, bounded execution, and independent review while the main thread leads and accepts the final result.">
</p>

协调探索、执行和独立评审，让复杂任务按明确职责并行推进，由主 Agent 统一验收。

It is a value-based routing guide, not a mandatory pipeline.

## The team

- **Explorer（探索者）· Luna Medium · read-only** — gathers evidence across current web sources, documents, datasets, codebases, schemas, APIs, logs, and configuration.
- **Executor（执行者）· Luna High · workspace-write** — completes clear, bounded work, including substantial bounded implementation, after scope, acceptance checks, and safety boundaries are clear.
- **Reviewer（复审者）· Terra Medium · read-only** — independently checks stable code, reports, plans, analyses, data, and other artifacts from fresh context.

Every spawn must explicitly pass one of those three names through `agent_type`. `task_name` is only a label, and `default` is never a working role.

Luna keeps discovery economical and gives bounded execution a higher reasoning margin. Terra provides fresh, independent review while the main thread retains architecture decisions and final acceptance.

The TOML sandbox is a profile default, not a guaranteed isolation boundary: a live parent permission override can be reapplied to children. Use the task-scoped usage report to verify each session's effective sandbox.

## How routing works

- Use Team Mode when delegation, parallel work, context isolation, lower-cost execution, or independent review has clear value.
- Team Mode may use no subagents at all. The main thread handles straightforward work when an agent would add more coordination than value.
- Before every spawn, identify the material benefit and count briefing, inspection, waiting, and rework as coordination cost. Explicitly invoking Team Mode does not make a spawn mandatory.
- Give every child a dispatch packet with `Outcome`, `Benefit`, `Sources`, `Scope`, `Checks`, `Stop when`, and `Return`; keep the slice in the main thread if the packet is incomplete or the gain does not exceed coordination cost.
- When two or more independent slices are ready, prefer dispatching them in parallel. The team size is dynamic: there is no fixed number of agents and no required sequence.
- Give non-trivial read-only discovery to `Explorer`; the main thread can wait instead of repeating the same work.
- After discovery, the main thread chooses whether to continue directly or delegate.
- Use `Executor` for localized or substantial bounded implementation once architecture, acceptance, and safety decisions are clear. Keep novel architecture, weak or visual verification, export/compiler behavior, and high-consequence security or rollback judgment in the main thread.
- Use `Reviewer` only when fresh independent judgment has clear value. Start each new Reviewer with no inherited conversation and give it a concrete unresolved risk, exact evidence, checks already passed, and a bounded stop condition.
- Keep fan-out in the main thread; children do not create descendants under standard Team Mode.
- Parallelize only genuinely independent work and keep one writer per shared target.
- After a child error or interruption, inspect shared artifacts before retrying; recover usable work instead of automatically repeating it.
- The main thread inspects the actual sources, artifacts, changes, and verification before accepting delegated work.

Casual conversation, simple lookups, and tasks whose coordination cost exceeds the work stay in the main thread.

## Install

Install the Skill:

```bash
npx skills add oil-oil/codex-team-mode
```

The three working Agent profiles and the default-on `default` dispatch guard are separate from the Skill. Copy the four TOML templates in [`agents/`](./agents) to `~/.codex/agents/` for personal use or `<repository>/.codex/agents/` for one project. Onboarding runs only for first setup, missing profiles, or explicit repair and verification requests.

See [Custom Agent Profiles](./skills/team-mode/references/custom-agents.md) for exact filenames, safe installation, validation, repair, and model customization. Open a new Codex task or restart Codex if newly installed profiles do not appear immediately.

After onboarding, Codex reports what was installed and how to disable only the guard. Disabling it is a recoverable move of `default.toml` outside the active `agents` directory; the three working profiles remain installed.

## Use

The Skill can trigger automatically for substantial tasks, or you can invoke it directly:

```text
Use $team-mode for this task. Choose the smallest useful team, prefer parallel dispatch for independent slices, and keep unresolved decisions and final acceptance in the main thread.
```

You do not need to name every agent yourself. The main thread chooses the smallest useful team, adapts it to the task's value, and remains responsible for the combined result.

## Customize

You can change `model` and `model_reasoning_effort` in `agents/*.toml`. Preserve the role boundaries: Explorer and Reviewer stay read-only, mutation permissions remain with Executor, new reviews use fresh context, and final acceptance stays with the main thread.

## Repository layout

```text
codex-team-mode/
├── agents/                  # Three working profiles plus one dispatch guard
├── assets/readme/           # README visuals and editable source layers
├── skills/team-mode/        # Installable Skill
│   ├── agents/openai.yaml
│   ├── references/          # Profile setup and evaluation guidance
│   ├── scripts/usage_by_model.py
│   └── SKILL.md
├── tests/                   # Agent, routing, and usage regression tests
├── LICENSE
└── README.md
```

<p align="center">
  <a href="https://github.com/oil-oil/beautify-github-readme"><img src="./assets/readme/made-with-beautify.svg" width="300" alt="README made with beautify-github-readme"></a>
</p>

MIT License

## 配置、依赖与使用边界

需要宿主提供可用的子 Agent 创建、消息与等待工具；自定义角色依赖宿主支持。无独立账号配置。

不把创建用户侧新任务与内部子 Agent 混为一谈。并行写代码须划分文件责任，汇总前核对真实产物与冲突。

使用示例：

```text
用 team-mode 协作处理这个项目中互相独立的模块。
```
