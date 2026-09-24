#!/usr/bin/env python3
"""Summarize locally retained Codex token usage by model, task, and Agent."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable


RATE_DATE = "2026-09-24"
RATE_SOURCE = "https://learn.chatgpt.com/docs/pricing"
RATES = {
    "gpt-6-astra": {"input": 250.0, "cached": 25.0, "output": 1250.0},
    "gpt-6-sol": {"input": 50.0, "cached": 5.0, "output": 250.0},
    "gpt-6-luna": {"input": 2.5, "cached": 0.25, "output": 12.5},
    # 保留旧任务的模型识别，使用同一官方费率表中的当前 Standard 费率。
    "gpt-5.6-luna": {"input": 5.0, "cached": 0.5, "output": 30.0},
    "gpt-5.6-terra": {"input": 50.0, "cached": 5.0, "output": 300.0},
    "gpt-5.6-sol": {"input": 100.0, "cached": 10.0, "output": 500.0},
}

USAGE_FIELDS = ("input_tokens", "cached_input_tokens", "output_tokens", "reasoning_output_tokens")
TRACE_DATE_RE = re.compile(r"(?:^|[-_])(20\d{2})[-_](\d{2})[-_](\d{2})(?:T|[-_.]|$)")


def default_sessions_root() -> Path:
    codex_home = os.environ.get("CODEX_HOME")
    return (Path(codex_home) if codex_home else Path.home() / ".codex") / "sessions"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Report locally retained Codex token usage and estimated Standard credits by model."
    )
    period = parser.add_mutually_exclusive_group()
    period.add_argument("--days", type=int, default=1, help="纳入最近 N 个本地自然日创建的会话，汇总其保留用量；不是逐事件日账单（默认1天）。")
    period.add_argument("--all", action="store_true", help="Include every retained local session.")
    period.add_argument(
        "--task-id",
        metavar="ID|current",
        help="Include one root task and its subagents; 'current' reads CODEX_THREAD_ID.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument("--by-agent", action="store_true", help="Also group usage by custom Agent role.")
    parser.add_argument("--by-session", action="store_true", help="Also show each root or subagent session separately.")
    parser.add_argument(
        "--sessions-root", type=Path, default=None,
        help="Override the sessions directory; an archive is added only when explicitly requested.",
    )
    parser.add_argument(
        "--archived-sessions-root", type=Path, default=None,
        help="Also scan this archived sessions directory.",
    )
    args = parser.parse_args()
    if not args.all and args.days < 1:
        parser.error("--days must be at least 1")
    if args.task_id == "current":
        args.task_id = os.environ.get("CODEX_THREAD_ID")
        if not args.task_id:
            parser.error("--task-id current requires CODEX_THREAD_ID")
    return args


def session_date(path: Path, root: Path) -> date | None:
    try:
        year, month, day = path.relative_to(root).parts[:3]
        return date(int(year), int(month), int(day))
    except (ValueError, IndexError):
        match = TRACE_DATE_RE.search(path.name)
        if match:
            try:
                return date(*(int(part) for part in match.groups()))
            except ValueError:
                pass
        # 文件没有可识别日期时留给 session_meta 的 timestamp 决定是否纳入，
        # 不用 mtime，因为复制到归档目录会改变它。
        return None


def trace_files(root: Path, cutoff: date | None) -> Iterable[Path]:
    for path in root.rglob("*.jsonl"):
        # 按会话创建日筛选；路径日期只是无元数据时间时的后备，
        # 避免归档复制位置或mtime改变统计范围。
        yield path


def nested_spawn(payload: dict[str, Any]) -> dict[str, Any]:
    source = payload.get("source")
    if not isinstance(source, dict):
        return {}
    subagent = source.get("subagent")
    if not isinstance(subagent, dict):
        return {}
    spawn = subagent.get("thread_spawn")
    return spawn if isinstance(spawn, dict) else {}


def read_trace_metadata(
    path: Path, root: Path | None = None, *, detailed: bool = False
) -> tuple[dict[str, Any], int]:
    malformed = 0
    first_meta: dict[str, Any] | None = None
    latest_timestamp: datetime | None = None
    first_meta_timestamp: datetime | None = None
    has_complete = False
    has_final = False
    valid_events = 0
    try:
        lines = path.open("r", encoding="utf-8")
    except OSError:
        return {}, malformed
    with lines:
        for line in lines:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                malformed += 1
                continue
            valid_events += 1
            payload = event.get("payload") or {}
            timestamp = parse_timestamp(event.get("timestamp") or payload.get("timestamp"))
            if timestamp and (latest_timestamp is None or timestamp > latest_timestamp):
                latest_timestamp = timestamp
            if event.get("type") == "event_msg":
                event_kind = payload.get("type")
                if event_kind == "task_complete":
                    has_complete = True
            if is_nonempty_assistant_final(event):
                has_final = True
            if event.get("type") != "session_meta" or first_meta is not None:
                continue
            first_meta = payload
            first_meta_timestamp = timestamp
            if not detailed:
                break
    if first_meta is None:
        return {}, malformed
    spawn = nested_spawn(first_meta)
    session_id = first_meta.get("id") or path.stem
    parent_thread_id = first_meta.get("parent_thread_id") or spawn.get("parent_thread_id")
    is_child = bool(parent_thread_id or spawn)
    role = first_meta.get("agent_role") or spawn.get("agent_role")
    metadata_timestamp = parse_timestamp(
        first_meta.get("timestamp") or first_meta.get("created_at")
    ) or first_meta_timestamp
    file_day = session_date(path, root) if root else session_date(path, path.parent)
    session_day = (metadata_timestamp.astimezone().date() if metadata_timestamp else file_day)
    return {
        "path": path,
        "session_id": session_id,
        "task_hint": first_meta.get("session_id"),
        "parent_thread_id": parent_thread_id,
        "agent_role": role or ("subagent/unknown" if is_child else "main"),
        "agent_path": first_meta.get("agent_path") or spawn.get("agent_path"),
        "cwd": first_meta.get("cwd"),
        "metadata_timestamp": metadata_timestamp,
        "latest_timestamp": latest_timestamp or metadata_timestamp,
        "session_day": session_day,
        "has_task_complete": has_complete,
        "has_final_report": has_final,
        "valid_events": valid_events,
    }, malformed


def resolve_trace_tasks(metadata: list[dict[str, Any]]) -> None:
    by_session = {item["session_id"]: item for item in metadata}

    def resolve(item: dict[str, Any]) -> str:
        task_hint = item.get("task_hint")
        if isinstance(task_hint, str) and task_hint:
            return task_hint
        current = item
        seen: set[str] = set()
        while True:
            session_id = str(current["session_id"])
            if session_id in seen:
                return session_id
            seen.add(session_id)
            parent = current.get("parent_thread_id")
            if not isinstance(parent, str) or not parent:
                return session_id
            parent_metadata = by_session.get(parent)
            if parent_metadata is None:
                return parent
            task_hint = parent_metadata.get("task_hint")
            if isinstance(task_hint, str) and task_hint:
                return task_hint
            current = parent_metadata

    for item in metadata:
        item["task_id"] = resolve(item)


def discover_traces(
    root: Path,
    cutoff: date | None,
    additional_roots: Iterable[Path] | None = None,
    diagnostics: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], int, int]:
    metadata: list[dict[str, Any]] = []
    file_count = 0
    malformed = 0
    roots = [root, *(additional_roots or [])]
    for scan_root in roots:
        if not scan_root.is_dir():
            continue
        for path in trace_files(scan_root, cutoff):
            file_count += 1
            item, item_malformed = read_trace_metadata(path, scan_root)
            malformed += item_malformed
            if item and (cutoff is None or item.get("session_day") is None
                         or item["session_day"] >= cutoff):
                item["_scan_root"] = scan_root
                metadata.append(item)

    # 普通会话只需读取首条 session_meta；只有 ID 冲突时才全文读取，用于比较
    # 最后时间、完成状态和有效事件数量。
    by_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in metadata:
        by_id[str(item["session_id"])].append(item)
    for candidates_for_id in by_id.values():
        if len(candidates_for_id) < 2:
            continue
        for index, item in enumerate(candidates_for_id):
            detailed_item, _ = read_trace_metadata(
                item["path"], item["_scan_root"], detailed=True
            )
            if detailed_item:
                detailed_item["_scan_root"] = item["_scan_root"]
                candidates_for_id[index].update(detailed_item)

    # 同一会话可能同时留在活动目录和归档目录；先选择最后事件更新的副本，
    # 同一终点再比较结束状态及信息完整性，避免旧完成记录覆盖后续续跑。
    candidates: dict[str, dict[str, Any]] = {}
    overwritten: list[dict[str, str]] = []
    for item in metadata:
        session_id = str(item["session_id"])
        current = candidates.get(session_id)
        if current is None:
            candidates[session_id] = item
            continue
        def rank(value: dict[str, Any]) -> tuple[datetime, int, int, int, int]:
            return (
                value.get("latest_timestamp") or datetime.min.replace(tzinfo=timezone.utc),
                int(bool(value.get("has_task_complete"))),
                int(bool(value.get("has_final_report"))),
                int(value.get("valid_events") or 0),
                value["path"].stat().st_size if isinstance(value.get("path"), Path) else 0,
            )
        if rank(item) > rank(current):
            kept, discarded = item, current
            candidates[session_id] = item
        else:
            kept, discarded = current, item
        overwritten.append({
            "session_id": session_id,
            "kept": str(kept["path"]),
            "discarded": str(discarded["path"]),
        })
    metadata = list(candidates.values())
    for item in metadata:
        item.pop("_scan_root", None)
    if diagnostics is not None:
        diagnostics["duplicate_session_files"] = len(overwritten)
        diagnostics["session_files_deduplicated"] = len(overwritten)
        diagnostics["session_file_overwrites"] = overwritten
    resolve_trace_tasks(metadata)
    by_session = {item["session_id"]: item for item in metadata}
    def depth(item: dict[str, Any]) -> int:
        current = item
        seen: set[str] = set()
        value = 0
        while True:
            sid = str(current.get("session_id"))
            if sid in seen:
                return value
            seen.add(sid)
            parent = current.get("parent_thread_id")
            if not parent or parent not in by_session:
                return value
            value += 1
            current = by_session[parent]
    for item in metadata:
        item["depth"] = depth(item)
    return metadata, file_count, malformed


def parse_timestamp(value: Any) -> datetime | None:
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(value, tz=timezone.utc)
        except (ValueError, OverflowError, OSError):
            return None
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def has_cumulative_usage(value: Any) -> bool:
    """判断 total_token_usage 是否足以证明它是累计计数。"""
    return isinstance(value, dict) and all(
        isinstance(value.get(field), (int, float)) for field in ("input_tokens", "output_tokens")
    )


def is_nonempty_assistant_final(event: dict[str, Any]) -> bool:
    """只把实际的 assistant final 文本视为最终交接。"""
    payload = event.get("payload") or {}
    if not isinstance(payload, dict):
        return False
    candidates = [payload]
    # CLI 同时会写入 response_item，以及包含同一 AgentMessage 的
    # event_msg/item_completed；两种都是实际的 assistant final 证据。
    nested = payload.get("item")
    if isinstance(nested, dict):
        candidates.append(nested)
    for candidate in candidates:
        if candidate.get("phase") != "final_answer" and candidate.get("channel") != "final":
            continue
        is_assistant = candidate.get("role") == "assistant" or candidate.get("type") == "AgentMessage"
        if not is_assistant:
            continue
        content = candidate.get("content")
        if isinstance(content, str) and content.strip():
            return True
        if isinstance(content, list) and any(
            isinstance(part, dict) and isinstance(part.get("text"), str) and part["text"].strip()
            for part in content
        ):
            return True
    return False


def resolve_requested_task(metadata: list[dict[str, Any]], requested_id: str | None) -> str | None:
    if requested_id is None:
        return None
    for item in metadata:
        if item["session_id"] == requested_id:
            return str(item["task_id"])
    return requested_id


def blank_usage() -> dict[str, int]:
    return {"events": 0, "input": 0, "cached": 0, "output": 0, "reasoning": 0}


def add_usage(target: dict[str, int], usage: dict[str, Any]) -> None:
    target["events"] += 1
    target["input"] += int(usage.get("input_tokens") or 0)
    target["cached"] += int(usage.get("cached_input_tokens") or 0)
    target["output"] += int(usage.get("output_tokens") or 0)
    target["reasoning"] += int(usage.get("reasoning_output_tokens") or 0)


def merge_usage(target: dict[str, int], source: dict[str, int]) -> None:
    for key in target:
        target[key] += source[key]


def scan(
    root: Path,
    cutoff: date | None,
    task_id: str | None = None,
    archived_root: Path | None = None,
    diagnostics: dict[str, Any] | None = None,
) -> tuple[
    dict[str, dict[str, int]],
    dict[str, dict[str, int]],
    list[dict[str, Any]],
    int,
    int,
    int,
    str | None,
]:
    by_model: dict[str, dict[str, int]] = defaultdict(blank_usage)
    by_agent: dict[str, dict[str, int]] = defaultdict(blank_usage)
    sessions: list[dict[str, Any]] = []
    extra_roots = [archived_root] if archived_root is not None else []
    metadata, file_count, malformed_lines = discover_traces(
        root, cutoff, extra_roots, diagnostics
    )
    resolved_task_id = resolve_requested_task(metadata, task_id)
    included_count = 0

    for trace in metadata:
        if resolved_task_id is not None and trace["task_id"] != resolved_task_id:
            continue
        path = trace["path"]
        included_count += 1
        model: str | None = None
        effort: str | None = None
        usage_by_segment: dict[tuple[str, str | None], dict[str, int]] = defaultdict(blank_usage)
        timestamps: list[datetime] = []
        sandboxes: set[str] = set()
        approvals: set[str] = set()
        interrupted_count = 0
        task_complete = False
        final_report_present = False
        last_turn_final_report_present = False
        last_terminal: str | None = None
        skipped_duplicates = 0
        try:
            lines = path.open("r", encoding="utf-8")
        except OSError:
            continue
        seen_metadata = False
        previous_snapshots: dict[tuple[str, str | None], tuple[str, str] | None] = {}
        with lines:
            for line in lines:
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    if seen_metadata:
                        malformed_lines += 1
                    continue
                payload = event.get("payload") or {}
                timestamp = parse_timestamp(event.get("timestamp") or payload.get("timestamp"))
                if timestamp:
                    timestamps.append(timestamp)
                if event.get("type") == "session_meta":
                    seen_metadata = True
                elif event.get("type") == "turn_context":
                    next_model = payload.get("model") or model
                    next_effort = payload.get("effort")
                    if (next_model, next_effort) != (model, effort):
                        previous_snapshots.clear()
                    model = next_model
                    effort = next_effort
                    sandbox = payload.get("sandbox_policy")
                    if isinstance(sandbox, dict):
                        sandbox = sandbox.get("type")
                    if isinstance(sandbox, str) and sandbox:
                        sandboxes.add(sandbox)
                    approval = payload.get("approval_policy")
                    if isinstance(approval, str) and approval:
                        approvals.add(approval)
                elif event.get("type") == "event_msg":
                    event_kind = payload.get("type")
                    if event_kind == "task_complete":
                        task_complete = True
                        last_terminal = "completed"
                    elif event_kind == "task_started":
                        task_complete = False
                        last_turn_final_report_present = False
                        last_terminal = None
                        # 新一轮可能重发上一轮累计快照；task_started本身不是计数重置。
                    elif event_kind == "turn_aborted":
                        interrupted_count += 1
                        last_terminal = "interrupted"
                if is_nonempty_assistant_final(event):
                    final_report_present = True
                    last_turn_final_report_present = True
                if (
                    event.get("type") == "event_msg"
                    and payload.get("type") == "token_count"
                ):
                    usage = ((payload.get("info") or {}).get("last_token_usage"))
                    if usage:
                        session_model = model or "unknown"
                        segment = (session_model, effort)
                        total_usage = (payload.get("info") or {}).get("total_token_usage")
                        # last_token_usage 没有累计证据时可能代表两个真实轮次；
                        # 只有完整 total 与 last 同时相邻相等，才认定为重复快照。
                        snapshot_key = (
                            json.dumps(total_usage, sort_keys=True, separators=(",", ":"))
                            if has_cumulative_usage(total_usage) else ""
                        )
                        usage_key = json.dumps(usage, sort_keys=True, separators=(",", ":"))
                        snapshot = (snapshot_key, usage_key)
                        previous = previous_snapshots.get(segment)
                        if snapshot_key and previous == snapshot:
                            skipped_duplicates += 1
                            continue
                        previous_snapshots[segment] = snapshot if snapshot_key else None
                        add_usage(usage_by_segment[segment], usage)
        role = trace["agent_role"]
        started = min(timestamps) if timestamps else None
        ended = max(timestamps) if timestamps else None
        terminal = last_terminal or "incomplete"
        if diagnostics is not None:
            diagnostics.setdefault("session_statuses", []).append({
                "session_id": trace["session_id"],
                "terminal_status": terminal,
                "depth": trace.get("depth", 0),
                "task_complete": task_complete,
                "final_report_present": final_report_present,
                "last_turn_final_report_present": last_turn_final_report_present,
            })
        if not usage_by_segment:
            usage_by_segment[(model or "unknown", effort)]
        for (session_model, session_effort), usage in usage_by_segment.items():
            merge_usage(by_model[session_model], usage)
            merge_usage(by_agent[f"{role} · {session_model}"], usage)
            sessions.append({
                **trace,
                "model": session_model,
                "effort": session_effort,
                "usage": usage,
                "started_at": started.isoformat().replace("+00:00", "Z") if started else None,
                "ended_at": ended.isoformat().replace("+00:00", "Z") if ended else None,
                "elapsed_seconds": (ended - started).total_seconds() if started and ended else None,
                "terminal_status": terminal,
                "final_report_present": final_report_present,
                "last_turn_final_report_present": last_turn_final_report_present,
                "task_complete": task_complete,
                "interrupted_count": interrupted_count,
                "skipped_duplicate_events": skipped_duplicates,
                "effective_sandbox": sorted(sandboxes),
                "approval_policy": sorted(approvals),
            })
    return (
        dict(by_model),
        dict(by_agent),
        sessions,
        file_count,
        included_count,
        malformed_lines,
        resolved_task_id,
    )


def usage_row(name: str, usage: dict[str, int]) -> dict[str, Any]:
    uncached = max(usage["input"] - usage["cached"], 0)
    total = usage["input"] + usage["output"]
    rate = RATES.get(name.split(" · ")[-1])
    credits = None
    credit_breakdown = None
    if rate:
        credit_breakdown = {
            "uncached_input": uncached * rate["input"] / 1_000_000,
            "cached_input": usage["cached"] * rate["cached"] / 1_000_000,
            "output": usage["output"] * rate["output"] / 1_000_000,
        }
        credits = sum(credit_breakdown.values())
    return {
        "name": name,
        "token_events": usage["events"],
        "total_processed_tokens": total,
        "input_tokens": usage["input"],
        "cached_input_tokens": usage["cached"],
        "uncached_input_tokens": uncached,
        "output_tokens": usage["output"],
        "reasoning_output_tokens": usage["reasoning"],
        "estimated_standard_credit_breakdown": credit_breakdown,
        "estimated_standard_credits": credits,
        "effective_processed_tokens_per_credit": total / credits if credits else None,
    }


def rate_card_rows() -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for model, rate in RATES.items():
        result.append({
            "model": model,
            "credits_per_million_tokens": {
                "uncached_input": rate["input"],
                "cached_input": rate["cached"],
                "output": rate["output"],
            },
            "tokens_per_credit": {
                "uncached_input": 1_000_000 / rate["input"],
                "cached_input": 1_000_000 / rate["cached"],
                "output": 1_000_000 / rate["output"],
            },
        })
    return result


def usage_summary(data: list[dict[str, Any]]) -> dict[str, Any]:
    total_tokens = sum(row["total_processed_tokens"] for row in data)
    known_credits = sum(row["estimated_standard_credits"] or 0 for row in data)
    unpriced_rows = [row for row in data if row["estimated_standard_credits"] is None]
    unpriced_tokens = sum(row["total_processed_tokens"] for row in unpriced_rows)
    known_tokens = total_tokens - unpriced_tokens
    return {
        "token_events": sum(row["token_events"] for row in data),
        "total_processed_tokens": total_tokens,
        "input_tokens": sum(row["input_tokens"] for row in data),
        "cached_input_tokens": sum(row["cached_input_tokens"] for row in data),
        "uncached_input_tokens": sum(row["uncached_input_tokens"] for row in data),
        "output_tokens": sum(row["output_tokens"] for row in data),
        "reasoning_output_tokens": sum(row["reasoning_output_tokens"] for row in data),
        "estimated_standard_credits": known_credits,
        "estimated_standard_credits_complete": not unpriced_rows,
        "known_processed_tokens": known_tokens,
        "effective_processed_tokens_per_credit": (
            known_tokens / known_credits if known_credits and not unpriced_tokens else None
        ),
        "unpriced_models": [row["name"] for row in unpriced_rows],
        "unpriced_processed_tokens": unpriced_tokens,
        "unpriced_token_events": sum(row["token_events"] for row in unpriced_rows),
    }


def add_credit_shares(result: list[dict[str, Any]]) -> list[dict[str, Any]]:
    known_total = sum(row["estimated_standard_credits"] or 0 for row in result)
    for row in result:
        credits = row["estimated_standard_credits"]
        row["known_credit_share_percent"] = (credits / known_total * 100) if credits is not None and known_total else None
    return result


def rows(source: dict[str, dict[str, int]]) -> list[dict[str, Any]]:
    return add_credit_shares([usage_row(name, usage) for name, usage in sorted(source.items())])


def session_rows(sessions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for session in sessions:
        role = session["agent_role"]
        model = session["model"]
        result.append({
            **usage_row(f"{role} · {model}", session["usage"]),
            "session_id": session["session_id"],
            "task_id": session["task_id"],
            "parent_thread_id": session["parent_thread_id"],
            "agent_role": role,
            "agent_path": session["agent_path"],
            "model": model,
            "effort": session["effort"],
            "cwd": session["cwd"],
            "started_at": session.get("started_at"),
            "ended_at": session.get("ended_at"),
            "elapsed_seconds": session.get("elapsed_seconds"),
            "terminal_status": session.get("terminal_status", "incomplete"),
            "final_report_present": session.get("final_report_present", False),
            "task_complete": session.get("task_complete", False),
            "last_turn_final_report_present": session.get("last_turn_final_report_present", False),
            "interrupted_count": session.get("interrupted_count", 0),
            "skipped_duplicate_events": session.get("skipped_duplicate_events", 0),
            "effective_sandbox": session.get("effective_sandbox", []),
            "approval_policy": session.get("approval_policy", []),
            "depth": session.get("depth", 0),
        })
    result.sort(key=lambda row: (row["agent_path"] or "/root", row["session_id"], row["model"]))
    return add_credit_shares(result)


def print_table(title: str, data: list[dict[str, Any]]) -> None:
    print(title)
    print(
        f"{'Model / Agent':<34} {'Processed':>14} {'Uncached':>12} {'Cached':>12} "
        f"{'Output':>11} {'Reason':>10} {'Credits*':>11} {'Tok/Credit':>12} {'Share':>8}"
    )
    print("-" * 136)
    for row in data:
        credits = row["estimated_standard_credits"]
        share = row["known_credit_share_percent"]
        tokens_per_credit = row["effective_processed_tokens_per_credit"]
        credits_text = f"{credits:,.2f}" if credits is not None else "n/a"
        share_text = f"{share:.2f}%" if share is not None else "n/a"
        tokens_per_credit_text = f"{tokens_per_credit:,.0f}" if tokens_per_credit is not None else "n/a"
        print(
            f"{row['name']:<34} "
            f"{row['total_processed_tokens']:>14,} "
            f"{row['uncached_input_tokens']:>12,} "
            f"{row['cached_input_tokens']:>12,} "
            f"{row['output_tokens']:>11,} "
            f"{row['reasoning_output_tokens']:>10,} "
            f"{credits_text:>11} "
            f"{tokens_per_credit_text:>12} "
            f"{share_text:>8}"
        )
    summary = usage_summary(data)
    effective = summary["effective_processed_tokens_per_credit"]
    effective_text = f"{effective:,.0f}" if effective is not None else "n/a"
    print("-" * 136)
    print(
        f"{'TOTAL':<34} "
        f"{summary['total_processed_tokens']:>14,} "
        f"{summary['uncached_input_tokens']:>12,} "
        f"{summary['cached_input_tokens']:>12,} "
        f"{summary['output_tokens']:>11,} "
        f"{summary['reasoning_output_tokens']:>10,} "
        f"{summary['estimated_standard_credits']:>11,.2f} "
        f"{effective_text:>12} "
        f"{'100.00%':>8}"
    )
    print()


def print_session_table(data: list[dict[str, Any]]) -> None:
    print("By session")
    print(
        f"{'Role / Model':<26} {'Agent path':<22} {'Status':<11} {'Elapsed':>8} "
        f"{'Sandbox':<16} {'Processed':>11} {'Uncached':>10} {'Cached':>10} {'Output':>9} {'Credits*':>10}"
    )
    print("-" * 144)
    for row in data:
        credits = row["estimated_standard_credits"]
        credits_text = f"{credits:,.2f}" if credits is not None else "n/a"
        elapsed = f"{row['elapsed_seconds']:.1f}s" if row.get("elapsed_seconds") is not None else "n/a"
        sandbox = ",".join(row.get("effective_sandbox") or []) or "n/a"
        print(
            f"{row['name']:<26} {(row['agent_path'] or '/root'):<22} "
            f"{row.get('terminal_status', 'incomplete'):<11} {elapsed:>8} {sandbox:<16} "
            f"{row['total_processed_tokens']:>11,} {row['uncached_input_tokens']:>10,} "
            f"{row['cached_input_tokens']:>10,} {row['output_tokens']:>9,} {credits_text:>10}"
        )
    print()


def print_rate_card() -> None:
    print("Standard rate card · credits per 1M tokens / tokens per credit")
    print(
        f"{'Model':<18} {'Uncached cr':>11} {'Cached cr':>10} {'Output cr':>10} "
        f"{'Uncached tok/cr':>15} {'Cached tok/cr':>15} {'Output tok/cr':>14}"
    )
    print("-" * 110)
    for row in rate_card_rows():
        rates = row["credits_per_million_tokens"]
        equivalents = row["tokens_per_credit"]
        print(
            f"{row['model']:<18} {rates['uncached_input']:>10,.3f} {rates['cached_input']:>10,.3f} "
            f"{rates['output']:>10,.3f} {equivalents['uncached_input']:>14,.0f} "
            f"{equivalents['cached_input']:>15,.0f} {equivalents['output']:>14,.0f}"
        )
    print()


def unique_session_rows(data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """按会话去重，避免一个会话的多个模型段放大状态统计。"""
    result: dict[str, dict[str, Any]] = {}
    for row in data:
        result.setdefault(str(row["session_id"]), row)
    return list(result.values())


def main() -> int:
    args = parse_args()
    root = (args.sessions_root or default_sessions_root()).expanduser().resolve()
    archived_root = args.archived_sessions_root.expanduser().resolve() if args.archived_sessions_root else None
    if args.sessions_root is None and archived_root is None:
        candidate = root.parent / "archived_sessions"
        if candidate.is_dir():
            archived_root = candidate
    if not root.is_dir():
        print(f"Sessions directory not found: {root}", file=sys.stderr)
        return 2

    cutoff = None if args.all or args.task_id else date.today() - timedelta(days=args.days - 1)
    diagnostics: dict[str, Any] = {}
    (
        by_model,
        by_agent,
        sessions,
        file_count,
        included_count,
        malformed,
        resolved_task_id,
    ) = scan(root, cutoff, args.task_id, archived_root, diagnostics)
    if args.task_id and not included_count:
        print(f"Task not found in retained local sessions: {args.task_id}", file=sys.stderr)
        return 2
    model_rows = rows(by_model)
    agent_rows = rows(by_agent) if args.by_agent else []
    all_session_details = session_rows(sessions)
    detailed_sessions = all_session_details if args.by_session else []
    if resolved_task_id:
        period = f"task {resolved_task_id}"
    else:
        period = "all retained sessions" if cutoff is None else f"sessions created {cutoff.isoformat()} through {date.today().isoformat()} (local dates)"
    limitations = [
        "Local retained sessions only; ephemeral and unavailable remote sessions are excluded.",
        "--days filters session creation dates in local time and sums retained session usage; it is not an event-time daily bill. Use --task-id or --all for older resumed tasks.",
        "Credits use configured Standard rates and do not detect mixed Fast usage.",
        "Account limits and resets remain authoritative in Codex /usage.",
        "Runtime fields come from local trace events; completed means only that the session has task_complete, not that artifact quality is assured.",
    ]
    distinct_session_rows = unique_session_rows(all_session_details)
    status_rows = diagnostics.get("session_statuses") or distinct_session_rows
    status_counts = {status: sum(1 for row in status_rows if row.get("terminal_status") == status)
                     for status in ("completed", "interrupted", "incomplete")}
    max_depth = max((row.get("depth", 0) for row in status_rows), default=0)
    summary = usage_summary(model_rows)
    diagnostics["skipped_duplicate_events"] = sum(
        row.get("skipped_duplicate_events", 0) for row in distinct_session_rows
    )

    if args.json:
        print(json.dumps({
            "period": period,
            "task_id": resolved_task_id,
            "requested_task_or_session_id": args.task_id,
            "date_filter_basis": "session_creation_local_date",
            "sessions_root": str(root),
            "archived_sessions_root": str(archived_root) if archived_root else None,
            "files_scanned": file_count,
            "session_files_included": included_count,
            "malformed_lines_skipped": malformed,
            "credit_rates_as_of": RATE_DATE,
            "credit_rate_source": RATE_SOURCE,
            "credit_rates": rate_card_rows(),
            "summary": summary,
            "models": model_rows,
            "agents": agent_rows,
            "sessions": detailed_sessions,
            "session_status_counts": status_counts,
            "max_subagent_depth": max_depth,
            "diagnostics": diagnostics,
            "limitations": limitations,
        }, ensure_ascii=False, indent=2))
        return 0

    print(f"Codex local usage · {period}")
    archive_note = f" + archived {archived_root}" if archived_root else ""
    print(f"Scanned {file_count} session files ({root}{archive_note}) · included {included_count} · Standard credit rates as of {RATE_DATE}")
    if diagnostics.get("duplicate_session_files"):
        print(f"Deduplicated {diagnostics['duplicate_session_files']} duplicate session files")
    if diagnostics.get("skipped_duplicate_events"):
        print(f"Skipped {diagnostics['skipped_duplicate_events']} adjacent duplicate token snapshots")
    print("Processed tokens = input (cached included) + output; reasoning is already included in output.")
    print()
    print_table("By model", model_rows)
    if args.by_agent:
        print_table("By Agent role", agent_rows)
    if args.by_session:
        print_session_table(detailed_sessions)
    print_rate_card()
    print(f"Rate source: {RATE_SOURCE}")
    print("* Tok/Credit is the observed processed-token ratio for that row, not a universal conversion. ")
    print("* Estimated Standard credits. " + " ".join(limitations))
    if not summary["estimated_standard_credits_complete"]:
        print(
            "* Unknown model pricing is excluded from the credit estimate: "
            f"{summary['unpriced_processed_tokens']:,} processed tokens across "
            f"{', '.join(summary['unpriced_models'])}."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
