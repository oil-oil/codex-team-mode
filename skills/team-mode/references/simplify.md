# Simplify

Use this route before committing a code change, or when the user asks to simplify code. Review the changed code and related documentation, not the whole repository. It is not a pass after every edit.

Look for complexity that makes the result harder to understand or change: unnecessary gates and special cases, fallback chains that obscure intended behavior or hide failures, stale documentation that would mislead the next agent or maintainer, oversized files, and responsibilities that would be clearer as components or functions. Notice duplication and needless abstraction too. These are leads, not required findings; keep useful safeguards and avoid splitting code solely to make files shorter.

Assign a fresh `Reviewer` the changed work and intended behavior. Ask it to identify concrete simplifications with locations and reasons, without suggesting a diagnosis. The reviewer may save a Markdown report but leaves the code unchanged. The main agent makes worthwhile fixes or assigns them to `Executor` before committing. If the reviewer finds nothing useful, leave the code alone.
