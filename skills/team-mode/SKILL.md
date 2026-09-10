---
name: team-mode
description: "为复杂开发、研究、文档、数据和内容任务协调职责明确的子 Agent，按需要分配探索、执行与独立评审。适用于任务可独立拆分、并行或隔离上下文能改善结果的场景；主 Agent 保留未决判断与最终验收，不用于简单问答和小任务。"
---

# Team Mode

Lead the task in the main thread. Use the smallest useful parallel set of subagents to isolate noisy work, reduce expensive main-agent context, run independent work in parallel, or obtain a fresh review. Do not turn the roles into a mandatory pipeline.

## Dispatch Gate

Every `spawn_agent` call must explicitly pass `agent_type` as exactly one of `Explorer`, `Executor`, or `Reviewer`.

- Never omit `agent_type` and never pass `default`. The `default` profile is a fail-closed dispatch guard, not a working Agent.
- Never use `task_name` to select a profile; it only labels the child thread.
- If the intended custom profile is unavailable, keep the work in the main thread or repair the profiles. Do not silently use a generic child.
- If a child returns the dispatch-guard message or its trace shows `default` / `subagent/unknown`, reject its output and respawn only after selecting the intended custom profile explicitly.

Read [references/custom-agents.md](references/custom-agents.md) only when installing, repairing, or verifying the three working profiles and the `default` guard. The controlled onboarding self-test described there is the only time Team Mode deliberately omits `agent_type`.

## One-Time Onboarding

Do not inspect Agent files, load onboarding instructions, or repeat setup explanations during normal Team Mode routing. Treat the active `spawn_agent.agent_type` choices and descriptions as runtime readiness evidence. When all three working profiles are available and `default` is described as the dispatch guard, skip onboarding without mentioning it.

Only read [references/custom-agents.md](references/custom-agents.md) and start onboarding when a required profile or guard is unavailable, or when the user explicitly asks to install, repair, verify, move, disable, or customize them. Get authorization before writing personal or project configuration. After a successful setup or repair, tell the user once what was installed, which models are assigned, that the guard affects omitted/default subagent dispatches in its installation scope, when restart or a new task is required, and how to disable or restore only the guard without removing the three working profiles.

## Required Rules

- When this Skill activates, immediately send one brief commentary update in the user's language, prefixed with `👾`. For Chinese, say `👾 已开启小队模式。`; translate naturally for other languages. Announce it once per task, not before every subagent call.
- Activating Team Mode does not require spawning any subagent. Keep genuinely short, single-slice work in the main thread when delegation would cost more than execution.
- For every substantial task, perform a brief decomposition pass before working locally. If two or more slices can finish independently with disjoint write ownership or read-only access, dispatch them together unless briefing and inspection clearly cost more than the saved time.
- After unresolved architecture, product, safety, scope, and acceptance decisions are fixed, perform an execution checkpoint before the main thread starts substantial mutable work. Identify bounded, independently verifiable write slices and route useful slices to one or more Executors when parallelism, context isolation, or lower-cost execution creates material value. Keep a slice in the main thread only when ownership cannot be isolated, verification depends on main-thread judgment, or delegation brings no meaningful gain; record the reason briefly.
- Before each spawn, identify one material benefit: useful parallelism, context isolation, lower-cost bounded execution, or independent judgment. Count briefing, inspection, rework, and waiting as coordination cost, but do not use coordination cost as a generic reason to serialize substantial independent work.
- Keep all routing and fan-out in the main thread. Under standard Team Mode, children never spawn descendants; they return evidence, artifacts, or blockers to the parent. Treat an explicit user request for recursive delegation as a separate scope expansion with its own permission, depth, and usage decision.
- Use `fork_turns="none"` by default and always for a new `Reviewer`.
- Keep unresolved user intent, product, editorial, architecture, and safety decisions, plus final acceptance, in the main thread.
- Assign one current writer to every file, shared artifact, interactive session, or mutable-system boundary. Parallel writers in one working tree are encouraged only when ownership is disjoint and stable; tell every writer that others are active and unrelated edits must be preserved. When ownership changes, the main thread must stop the previous writer and state the handoff before the new writer starts.
- Inspect the actual artifacts, sources, diffs, and verification output before accepting delegated work.
- If a child errors, times out, or is interrupted, inspect shared artifacts and trace evidence before retrying. Retry a transient failure at most once and only when no usable result exists; otherwise recover in the main thread or re-scope the remaining work.
- Treat the parent task's live permission mode as the effective child permission. Do not infer read-only isolation from TOML alone; use the onboarding or diagnostic verification in the reference when permissions need confirmation.

When the user asks to evaluate Team Mode itself, compare models or reasoning effort, or measure whether delegation was worthwhile, read [references/evaluation.md](references/evaluation.md) before designing the trial.

## Dispatch Contract

Before every spawn, make the brief self-contained with these labeled fields:

- `Outcome`: the independently finishable result the child must return.
- `Benefit`: the material advantage over keeping this slice in the main thread.
- `Sources`: every path, URL, dataset, or raw artifact required for factual work.
- `Scope`: allowed reads or writes, ownership, exclusions, and external-action authority.
- `Checks`: acceptance criteria and validation the child owns.
- `Stop when`: the bounded completion, blocker, or evidence threshold that ends the turn.
- `Return`: the concise report or artifact format expected by the parent.

Do not spawn while `Outcome`, `Benefit`, required `Sources`, `Checks`, or `Stop when` is missing. Keep a slice in the main thread when it is not independently finishable. For a parallel batch, compare the batch's combined wall-clock and context benefit against shared briefing, waiting, inspection, and possible rework instead of rejecting each child in isolation.

For a `Reviewer`, also name one concrete `Unresolved risk`, the exact `Evidence` to inspect, `Checks already passed`, and `Do not repeat`. Ask for findings from that packet first and require a usable partial verdict if the stop condition arrives before exhaustive review.

## Route The Work

- `Explorer`（Luna Medium）: use for non-trivial read-only discovery. Give separate Explorers independent evidence slices and do not repeat their work in the main thread.
- `Executor`（Luna High）: use for both localized and substantial bounded execution after the main thread has fixed unresolved architecture, product, safety, scope, and acceptance decisions. Split independent modules, tests, migrations, documentation, or artifact production across multiple Executors with disjoint ownership.
- Main thread: keep the critical slice when it needs novel architecture, weak or visual verification, export/compiler design, security or rollback judgment, or when a plausible false success would be costly.
- `Reviewer`（Terra Medium）: use fresh read-only context for one concrete unresolved risk. For substantial code changes, use the Simplify review workflow below.

Do not wait for all discovery to finish before dispatching already-bounded independent slices. Let the main thread fix unresolved decisions, then actively look for additional independent execution slices.

## Simplify Review For Substantial Code Changes

After a substantial code change is stable and targeted checks pass, run a Simplify-style review when any of these applies:

- production code changed across multiple modules or three or more files;
- shared APIs, state, persistence, concurrency, performance-sensitive paths, or cross-cutting behavior changed;
- the diff is large enough that one linear review could easily miss reuse, dead code, or regression risks;
- the user explicitly asks for review, cleanup, simplification, or high confidence.

Cover three independent lenses: code quality, performance, and reuse. When the lenses can be reviewed independently and parallel capacity is useful, launch one fresh `Reviewer` per lens in the same batch. Otherwise use the smallest number of Reviewers that can keep the lenses distinct without weakening the review.

Reviewers only report severity-ordered findings with paths, evidence, and the smallest behavior-preserving fix. They do not edit, format, commit, or repeat checks that already passed. The main thread validates and aggregates findings, applies accepted targeted fixes, and reruns the relevant checks. Skip broad refactors, public API changes, or speculative cleanup and report why.

For smaller changes, use one risk-focused Reviewer only when independent judgment adds clear value.

## Coordinate The Work

- Start with the smallest useful parallel batch, not automatically one Agent. Parallelize genuinely independent exploration, analysis, tests, triage, production, or review; do not duplicate work merely to keep Agents occupied.
- For coding tasks, explicitly test these split points before choosing serial work: independent modules, implementation versus tests, code versus documentation, separate platform targets, and separate verification surfaces.
- Before execution, state plainly what the result should be, what may be touched, what must remain unchanged, and how completion will be checked. Revise these requirements if new evidence conflicts with them.
- Verify in proportion to risk. Use independent review for complex, consequential, or difficult-to-check results rather than for every task.
- Reuse passed checks as evidence. Do not ask another Agent to repeat broad validation unless the integrity or relevance of those checks is itself the unresolved risk.

When a task depends on live UI, browser, device, or other interactive state that code inspection and automated checks cannot prove reliably, read [references/interactive-testing.md](references/interactive-testing.md). Do not load it for tasks that can be verified from code.

## Context And Reuse

- Give each new subagent a compact, self-contained brief containing only the objective, relevant sources or paths, scope, authority, exclusions, intended result, required checks, and return format. Never copy credentials into it.
- With `fork_turns="none"`, assume the child knows nothing from the parent conversation. Name every source artifact required for factual claims; if a source is missing, either provide its path, narrow the child to collecting that evidence, or keep the source-dependent slice in the main thread.
- Reuse an existing Explorer or executor when new work belongs to the same task, topic, business area, subsystem, artifact, or workstream and its prior context remains useful. Send only the new objective and changed constraints.
- Start fresh when prior context is stale or noisy, the role or authority changes, or independent judgment matters.
- Reuse a Reviewer only to clarify its existing report. Use a fresh Reviewer for a new review or for checking revised work.
- Do not give an Explorer an expected conclusion. Do not tell a Reviewer the prior debate, author, suspected findings, or desired verdict.

## Handle Findings

- Validate findings against the underlying sources, artifact, and intended outcome before acting.
- Let the main thread apply accepted repairs directly or delegate them according to scope, context, cost, and risk.
- When the risk assessment calls for independent review after consequential repairs, use a fresh Reviewer with only the updated artifact and neutral requirements.
- If a Reviewer crosses its `Stop when` condition without a usable return, request a partial verdict once, then interrupt it. Inspect the trace and existing evidence; do not automatically start another Reviewer.

## Inspect Local Usage

When the user asks for model or subagent consumption, run `python3 scripts/usage_by_model.py`. For the active task use `--task-id current --by-agent --by-session`; for broader history use `--days N` or `--all`, with `--json` when structured output helps. Report processed tokens plus uncached input, cached input, output, reasoning output, and estimated credits; do not hide the token totals behind credits. Treat reasoning as a subset of output and processed tokens as input plus output, so neither cached nor reasoning tokens are double-counted. Never present one universal credits-to-token conversion: use the bundled rate card because each model and token type has a different rate, and label the observed processed-tokens-per-credit value as workload-specific. This is an on-demand diagnostic, not part of normal routing. Report that local logs exclude ephemeral or unavailable remote sessions, configured credits assume Standard speed, and Codex `/usage` remains authoritative for account limits.

## Guardrails

- Preserve unrelated user work and obey applicable project, domain, and tool instructions.
- Delegation does not expand authority. Do not commit, publish, deploy, send messages, change external state, or handle sensitive data beyond the user's request.
- For current or factual research, prefer primary sources, record relevant dates, cite evidence, and distinguish fact from inference.
- Keep private-data exploration narrow and return only the minimum evidence needed.
- Resolve conflicting claims against the strongest available evidence and return one coherent result to the user.
