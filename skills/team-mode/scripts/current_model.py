#!/usr/bin/env python3
"""Best-effort lookup of the current task model from local Codex traces."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def codex_home() -> Path:
    configured = os.environ.get("CODEX_HOME")
    return Path(configured).expanduser() if configured else Path.home() / ".codex"


def parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed
    except ValueError:
        return None


def emit_unknown(reason: str) -> int:
    print(json.dumps({"status": "unknown", "reason": reason}, ensure_ascii=False))
    return 2


def main() -> int:
    task_id = os.environ.get("CODEX_THREAD_ID")
    if not task_id:
        return emit_unknown("CODEX_THREAD_ID is not set")

    home = codex_home()
    active_root = home / "sessions"
    archived_root = home / "archived_sessions"
    roots = [root for root in (active_root, archived_root) if root.is_dir()]
    candidates: list[tuple[datetime, str, str | None]] = []

    # Match the task ID in filenames before reading traces. Trace formats are internal,
    # so return unknown on failure instead of inferring the runtime model from config.
    for root in roots:
        for path in root.rglob(f"*{task_id}*.jsonl"):
            meta_id: str | None = None
            contexts: list[tuple[datetime, str, str | None]] = []
            try:
                with path.open("r", encoding="utf-8") as trace:
                    for line in trace:
                        try:
                            event = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        if not isinstance(event, dict):
                            continue
                        payload = event.get("payload") or {}
                        if not isinstance(payload, dict):
                            continue
                        if event.get("type") == "session_meta":
                            meta_id = payload.get("id") or payload.get("session_id")
                        elif event.get("type") == "turn_context":
                            model = payload.get("model")
                            timestamp = parse_time(event.get("timestamp") or payload.get("timestamp"))
                            if isinstance(model, str) and model and timestamp:
                                effort = payload.get("effort")
                                contexts.append((timestamp, model, effort if isinstance(effort, str) else None))
            except OSError:
                continue

            # Exclude subagents whose filename contains the root task ID.
            if meta_id != task_id:
                continue
            candidates.extend(contexts)

    if not candidates:
        return emit_unknown("No model record for the current task was found in local traces")

    observed_at, model, effort = max(candidates, key=lambda item: item[0])
    print(json.dumps({
        "status": "ok",
        "task_id": task_id,
        "model": model,
        "effort": effort,
        "observed_at": observed_at.isoformat(),
        "source": "local_codex_session_trace",
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
