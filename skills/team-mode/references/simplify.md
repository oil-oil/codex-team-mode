# Simplify

Use this route before committing a code change, or when the user asks to simplify code. Review the changed code and related documentation, not the whole repository. It is not a pass after every edit. Resolve the scope before dispatch and honor any narrower scope set by the parent or user. Read applicable project instructions such as `AGENTS.md` and follow the repository's conventions. If there is no substantive code change and no explicit request to simplify documentation, report that there is nothing to simplify rather than widening the scope.

Look for complexity that makes the result harder to understand or change: unnecessary gates and special cases, fallback chains that obscure intended behavior or hide failures, stale documentation that would mislead the next agent or maintainer, oversized files, and responsibilities that would be clearer as components or functions. Notice duplication and needless abstraction too. These are leads, not required findings; keep useful safeguards and avoid splitting code solely to make files shorter.

Choose the number of fresh `Reviewer` agents by the number of independent review lenses:

- One Reviewer is the default for a narrow diff or a single main concern. It can assess reuse, clarity, and efficiency together when those are all relevant.
- Use two or three Reviewers when a broader or riskier change has distinct lenses that can be reviewed independently. Examples include reuse of existing helpers, code structure and naming, and runtime or resource efficiency. Give each Reviewer the same resolved source scope, a different lens, and a concrete return format.
- Add more only when additional independent subsystems or risk areas justify separate work. Do not duplicate general reviews or split work by file count alone.

Ask each Reviewer to identify concrete, behavior-preserving simplifications with locations, reasons, and a proposed change. Reviewers report findings and leave source files unchanged in this pass. The installed Reviewer profile may still have workspace-write permission, so this is an instruction boundary, not a sandbox guarantee. Prefer returning findings inline; if a lasting report is needed, assign a unique report path outside the changed source diff.

The main agent selects findings and applies worthwhile changes or assigns an `Executor` with explicit write ownership. Preserve observable outputs, errors, side effects, ordering, trust-boundary validation, data-loss protection, security checks, and accessibility behavior. If equivalence is uncertain, skip the proposed simplification.

After edits, run the validation required by the task and project, and report which checks actually ran and their results. If any reviewed file changes after the Simplify review, dispatch one fresh `Reviewer` to inspect the resulting diff for correctness and omissions. If the reviewed files do not change, the original Reviewer may also serve as the final reviewer only when its brief explicitly included correctness and omission checks. Otherwise, dispatch a fresh Reviewer for the final check. The main agent decides whether the result is ready to commit.
