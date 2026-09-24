---
name: team-mode
description: "Use when a task may benefit from a bounded subagent for implementation, large-codebase discovery at task start, independent review, pre-commit code simplification, or expert work on complex decisions, modeling, automation, or repeated failures. The main agent chooses whether to delegate and accepts the result. Do not use for simple questions or short work with no meaningful review or delegation."
metadata:
  compatibility: "Codex with custom subagents; local model and usage diagnostics require Python 3.10+ and retained session logs."
---

# Team Mode

The main agent decomposes the user's task, decides what to delegate, and accepts the result. A task's size alone does not require subagents. On activation, send one brief commentary update in the user's language prefixed with `👾` (in Chinese: `👾 已开启小队模式。`).

## When to dispatch

Before dispatch, state the intended role and count, each child's independent scope, expected return, and write ownership. Keep write scopes separate whenever agents may edit the same workspace.

Delegate a defined part of the task when a child can make useful progress through implementation, codebase discovery, review, or expert work. The main agent owns how the parts fit together, unresolved product decisions, and final acceptance. There is no target number of agents or required sequence.

Choose the smallest count that covers the independent work. One child is the default for one bounded question or review lens. Add children only when each can work and report independently, with a distinct question, scope, or lens. A large diff alone is not a reason to fan out.

Two or three focused children are a useful starting point for genuinely multi-part work, not a fixed limit. Add more only when additional independent workstreams justify them. Consider coordination and usage overhead. Respect the host's active-agent limit; if parallel dispatch is unavailable, continue sequentially or inline without silently dropping coverage.

- `Explorer` — at the start of a new task, use only when the main agent needs to search a large codebase to locate the primary files and entry points. Small lookups and general research stay with the main agent. Read [Explore](references/explore.md) for this route.
- `Executor` — use when the intended result and file ownership are clear enough for independent implementation. Give each target one owner.
- `Reviewer` — use when the user asks for review or a completed result has a meaningful risk of unnoticed defects. Review the assigned result without steering toward a suspected answer; save a Markdown report when a lasting record helps.
- `ExpertAdvisor` — use for a complex architecture or high-impact decision, a problem unresolved after repeated attempts, or modeling or complex computer automation the main agent cannot handle well. Ask for an independent plan or assign the expert a concrete outcome to produce.

Before committing code, follow [Simplify](references/simplify.md). One fresh `Reviewer` can cover a narrow change. Use multiple Reviewers only when broader or riskier work has distinct, independent review lenses. Reviewers may share the same read-only source scope, but each saved report needs a unique path outside the changed source diff. Prefer returning findings directly when no lasting report is needed.

Reviewer assignments prohibit source edits; the installed `Reviewer` profile may still grant workspace-write permission, so this boundary is instruction-based. The main agent, or an `Executor` with explicit write ownership, chooses and applies worthwhile fixes.

If any reviewed file changes after the Simplify review, send the resulting diff to one fresh `Reviewer` for a final correctness and omission check. If no reviewed files change, the original Reviewer can serve as the final check only when its assignment also covered correctness and omissions. Otherwise, dispatch a fresh Reviewer for that final check. The main agent accepts the final result.

Name the intended `agent_type` explicitly. Other configured roles and models are allowed when appropriate. Model and effort defaults, plus the optional `default.toml` sentinel, are described in [profile setup](references/custom-agents.md); normal dispatch does not require reading it.

## Context and handoff

Start a new child with `fork_turns="none"` by default. Always use it for `Reviewer` and `ExpertAdvisor`, whose value depends on an independent view. Use it for `Explorer` too: a question and codebase path are usually enough.

An `Executor` may inherit a small number of recent parent turns when the assignment depends on decisions in that conversation that a short brief would likely omit. Use the smallest useful positive `fork_turns` value; inherit the full conversation only when the whole history is genuinely needed. Reuse an existing child for a direct continuation of its own assignment.

Give the child its assigned question or deliverable, relevant context, and scope. Include the broader user goal when it helps explain the assignment. Pass files, symptoms, and prior attempts as leads, not a fixed diagnosis or checklist. The child chooses its method within the assigned part; the main agent handles changes to the task breakdown and checks the returned work.

## Expert help

When stronger expertise would help, use `python3 scripts/current_model.py` if the parent model is unclear. Choose an available stronger model and supported effort for the model-free `ExpertAdvisor` profile.

Give it the decision or outcome, relevant context, evidence, constraints, and scope without presenting a proposed cause as fact. The expert may produce a plan or carry out assigned modeling or complex automation. Check its result before accepting it. If no stronger model is available, continue without claiming a stronger-model consultation.

A model fixed in a custom profile takes precedence over a spawn-time choice. See [profile setup](references/custom-agents.md) for model changes; do not assume an explicit model overrides `Explorer`, `Executor`, or `Reviewer`.

## Diagnostics

For a requested usage report, run `python3 scripts/usage_by_model.py`; read [evaluation guidance](references/evaluation.md) when evaluating Team Mode itself. For an interactive-state task that code inspection cannot establish, read [interactive testing guidance](references/interactive-testing.md).
