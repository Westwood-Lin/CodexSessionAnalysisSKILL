from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
from pathlib import Path
from typing import Any


INJECTED_MARKERS = (
    "<environment_context>",
    "<codex_internal_context",
    "<skills_instructions>",
    "<external_codex_apps_open_page>",
)


def message_text(payload: dict[str, Any]) -> str:
    parts: list[str] = []
    for item in payload.get("content") or []:
        if isinstance(item, dict):
            value = item.get("text") or item.get("input_text") or item.get("output_text")
            if isinstance(value, str):
                parts.append(value)
    return "\n".join(parts).strip()


def is_injected(text: str) -> bool:
    stripped = text.strip()
    return any(stripped.startswith(marker) for marker in INJECTED_MARKERS)


def redact(text: str) -> str:
    text = re.sub(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", "<EMAIL>", text, flags=re.I)
    text = re.sub(r"(?i)(pwd|password|secret|cred)\s*[:=]\s*\S+", r"\1=<REDACTED>", text)
    text = re.sub(r"(?i)(bearer\s+)[A-Za-z0-9._~-]+", r"\1<REDACTED>", text)
    text = re.sub(r"\b[0-9a-f]{8}-[0-9a-f-]{27,}\b", "<UUID>", text, flags=re.I)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def nested_tool_name(payload: dict[str, Any]) -> str:
    name = str(payload.get("name") or payload.get("tool_name") or payload.get("server") or "unknown")
    arguments = payload.get("arguments") or payload.get("input") or ""
    if isinstance(arguments, dict):
        arguments = json.dumps(arguments, ensure_ascii=False)
    if isinstance(arguments, str):
        match = re.search(r"tools\.([A-Za-z0-9_]+)\s*\(", arguments)
        if match:
            return match.group(1)
    return name


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--catalog", action="store_true")
    args = parser.parse_args()
    data = args.source.read_bytes()
    outer_types: collections.Counter[str] = collections.Counter()
    payload_types: collections.Counter[str] = collections.Counter()
    roles: collections.Counter[str] = collections.Counter()
    phases: collections.Counter[str] = collections.Counter()
    tools: collections.Counter[str] = collections.Counter()
    raw_user = 0
    excluded = 0
    prompts: list[str] = []
    assistant_messages = 0
    tool_calls = 0
    network_calls = 0
    timestamps: list[str] = []
    bad_json = 0
    for line in data.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            bad_json += 1
            continue
        outer_types[str(event.get("type") or "<none>")] += 1
        timestamp = event.get("timestamp")
        if isinstance(timestamp, str):
            timestamps.append(timestamp)
        payload = event.get("payload")
        if not isinstance(payload, dict):
            continue
        payload_type = str(payload.get("type") or "<none>")
        payload_types[payload_type] += 1
        role = str(payload.get("role") or "<none>")
        roles[role] += 1
        phase = str(payload.get("phase") or "<none>")
        phases[phase] += 1
        if payload_type == "message":
            text = message_text(payload)
            if role == "user":
                raw_user += 1
                if not text or is_injected(text):
                    excluded += 1
                else:
                    prompts.append(text)
            elif role == "assistant":
                assistant_messages += 1
        if payload_type.endswith("call"):
            tool_calls += 1
            tool = nested_tool_name(payload)
            tools[tool] += 1
            lowered = tool.casefold()
            if any(key in lowered for key in ("web", "browser", "http", "search", "cua", "tabbit")):
                network_calls += 1
    result: dict[str, Any] = {
        "source": args.source.resolve().as_uri(),
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "line_count": len(data.splitlines()),
        "bad_json": bad_json,
        "first_timestamp": min(timestamps) if timestamps else None,
        "last_timestamp": max(timestamps) if timestamps else None,
        "raw_user_messages": raw_user,
        "excluded_user_messages": excluded,
        "effective_user_prompts": len(prompts),
        "assistant_messages": assistant_messages,
        "tool_calls": tool_calls,
        "network_calls": network_calls,
        "outer_types": dict(outer_types),
        "payload_types": dict(payload_types),
        "roles": dict(roles),
        "phases": dict(phases),
        "tools": dict(tools),
    }
    if args.catalog:
        result["prompt_catalog"] = [
            {"id": index, "text": redact(text)[:700]} for index, text in enumerate(prompts, 1)
        ]
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
