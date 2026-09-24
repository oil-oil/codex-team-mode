# Explore

Use this route when starting a new task if the main agent needs a map of relevant code in a large codebase before implementation. The main agent defines the question that will unblock its task breakdown.

Dispatch `Explorer` with fresh context, the repository location, and the assigned question. Known files are search leads. The child follows the relevant entry points and code path without editing, then returns the primary files and symbols, how they connect, and brief evidence. Keep raw search output and unrelated architecture out of the handoff.

The main agent uses that map to decide what to do next. Handle a small, obvious lookup directly.
