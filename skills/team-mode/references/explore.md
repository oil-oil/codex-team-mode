# Explore

Use this route when starting a new task if the main agent needs a map of relevant code in a large codebase before implementation. The main agent defines the question that will unblock its task breakdown.

For one coherent question, dispatch one `Explorer` with fresh context, the repository location, and the assigned question. If the task needs maps of independent subsystems or answers to independent questions, dispatch one Explorer per track. Give each a distinct scope and return format; do not send multiple Explorers to produce the same general codebase map. Choose count by independent research tracks, not repository size alone. Two or three tracks are a useful starting point; add more only when each has a distinct question the main agent can combine.

Known files are search leads. Each Explorer follows relevant entry points and code paths without editing, then returns primary files and symbols, how they connect, and brief evidence. Keep raw search output and unrelated architecture out of each handoff. If parallel dispatch is unavailable or exceeds the host's active-agent limit, run tracks sequentially or do the remaining exploration in the main thread.

The main agent uses that map to decide what to do next. Handle a small, obvious lookup directly.
