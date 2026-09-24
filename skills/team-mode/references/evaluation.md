# Evaluate Team Mode

Read this only when the user asks to evaluate routing, model choice, cost, or practical value.

## Collect Evidence

1. Record the task goal, baseline, acceptance checks, and installed role-to-model mapping.
2. Check each child's actual role, model, and effort in the runtime trace. TOML files alone do not prove what ran.
3. Judge the returned artifact and the parent's inspection or rework, not the child's self-assessment.
4. Compare comparable work only. Do not create duplicate work just to fill a benchmark.

For local usage, run `python3 scripts/usage_by_model.py --task-id current --by-agent --by-session --json`. Separate uncached input, cached input, output, reasoning output, and estimated Standard credits. Local traces can omit sessions, and credit estimates are not invoices.

Record whether the fresh brief supplied the goal, source paths, scope, and checks the child needed. Missing evidence is a briefing issue before it is a model issue. Distinguish a completed lifecycle event from an actual final report and from main-agent acceptance. Inspect shared artifacts before retrying a failed or interrupted child.

## Interpret The Roles

- `Explorer` is useful only when the main agent explicitly needs a large-codebase file map. Measure whether it found the right primary files and reduced parent search.
- `Executor` is useful when scope and checks are clear. Measure accepted output, rework, and time saved through independent ownership.
- `Reviewer` should find material issues or confirm a meaningful risk was checked. A report with no findings is not automatically wasted work. Check a saved Markdown report when one was requested or useful.
- `ExpertAdvisor` should contribute an independently grounded plan or complete the assigned modeling or automation. Check the actual model and result before calling it stronger-model work.

Compare coordination cost, child usage, wall-clock effect, missed context, and final result. A fixed role's TOML model or effort takes precedence over spawn values; do not count a passed override request as an A/B trial without trace evidence.

Change routing or briefing before upgrading every role. Change a lasting profile only when repeated task-scoped evidence supports it, and update the template, installed file, documentation, and prior conclusions together.
