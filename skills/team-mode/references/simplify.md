# Simplify

Use this route when the user asks to simplify code or a completed change has a concrete complexity concern. It is not a required pass after every edit.

The main agent chooses the scope from the user's request or the relevant changed code. Look for unnecessary abstraction, duplicated logic or state, missed reuse, noisy comments, and avoidable inefficiency. These are possible angles, not a checklist or a required number of reviewers.

Use a fresh `Reviewer` when an independent look is useful. Ask for concrete findings tied to the selected code. The reviewer may save a Markdown report when useful but leaves the code under review unchanged. The main agent decides which small, behavior-preserving fixes to make or assigns a clearly owned fix to `Executor`. If nothing worthwhile is found, leave the code alone. Handle correctness defects through the normal review path.
