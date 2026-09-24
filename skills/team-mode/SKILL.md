---
name: team-mode
description: "Use when a task has a bounded part worth delegating, needs primary files located in a large codebase, calls for independent review or scoped code simplification, or needs stronger expertise for a complex decision, modeling, automation, or repeated failed repair. The main agent keeps decisions and final acceptance. Do not use for simple questions or short work that gains nothing from delegation."
metadata:
  compatibility: "Codex with custom subagents; local model and usage diagnostics require Python 3.10+ and retained session logs."
---

# Team Mode

The main agent decomposes the user's task, decides what to delegate, and accepts the result. A task's size alone does not require subagents. On activation, send one brief commentary update in the user's language prefixed with `👾` (in Chinese: `👾 已开启小队模式。`).

## When to dispatch

Delegate a defined part of the task when a child can make useful progress through implementation, codebase discovery, review, or expert work. The main agent owns how the parts fit together, unresolved product decisions, and final acceptance. There is no target number of agents or required sequence.

- `Explorer` — use only when the main agent explicitly needs to search a large codebase to locate the primary files and entry points. Small lookups and general research stay with the main agent. Read [Explore](references/explore.md) for this route.
- `Executor` — use when the intended result and file ownership are clear enough for independent implementation. Give each target one owner.
- `Reviewer` — use when the user asks for review or a completed result has a meaningful risk of unnoticed defects. Review the assigned result without steering toward a suspected answer; save a Markdown report when a lasting record helps. For code cleanup, read [Simplify](references/simplify.md).
- `ExpertAdvisor` — use for a complex architecture or high-impact decision, a problem unresolved after repeated attempts, or modeling or complex computer automation the main agent cannot handle well. Ask for an independent plan or assign the expert a concrete outcome to produce.

Name the intended `agent_type` explicitly. Other configured roles and models are allowed when appropriate. Model and effort defaults, plus the optional `default.toml` sentinel, are described in [profile setup](references/custom-agents.md); normal dispatch does not require reading it.

## Context and handoff

Start a new child with `fork_turns="none"` by default. Always use it for `Reviewer` and `ExpertAdvisor`, whose value depends on an independent view. Use it for `Explorer` too: a question and codebase path are usually enough.

An `Executor` may inherit a small number of recent parent turns when the assignment depends on decisions in that conversation that a short brief would likely omit. Use the smallest useful positive `fork_turns` value; inherit the full conversation only when the whole history is genuinely needed. Reuse an existing child for a direct continuation of its own assignment.

Give the child its assigned question or deliverable, relevant context, and scope. Include the broader user goal when it helps explain the assignment. Pass files, symptoms, and prior attempts as leads, not a fixed diagnosis or checklist. The child chooses its method within the assigned part; the main agent handles changes to the task breakdown and checks the returned work.

## Expert help

When stronger expertise would help, use `python3 scripts/current_model.py` if the parent model is unclear. Choose an available stronger model and supported effort for the model-free `ExpertAdvisor` profile. Give it the decision or outcome, relevant context, evidence, constraints, and scope without presenting a proposed cause as fact. The expert may produce a plan or carry out assigned modeling or complex automation. Check its result before accepting it. If no stronger model is available, continue without claiming a stronger-model consultation.

A model fixed in a custom profile takes precedence over a spawn-time choice. See [profile setup](references/custom-agents.md) for model changes; do not assume an explicit model overrides `Explorer`, `Executor`, or `Reviewer`.

## Diagnostics

For a requested usage report, run `python3 scripts/usage_by_model.py`; read [evaluation guidance](references/evaluation.md) when evaluating Team Mode itself. For an interactive-state task that code inspection cannot establish, read [interactive testing guidance](references/interactive-testing.md).
