"""Render a Claude Code session JSONL into readable Markdown.

Redactions (documented in transcript/README.md): <system-reminder> blocks (private
user configuration), the user's email address, and base64 image payloads.
Everything else — user messages, assistant reasoning, tool calls, tool results,
subagent reports — is reproduced verbatim.
"""
import json
import re
import sys
from datetime import datetime

SYSTEM_REMINDER = re.compile(r"<system-reminder>.*?</system-reminder>", re.S)
LOCAL_CAVEAT = re.compile(r"<local-command-caveat>.*?</local-command-caveat>", re.S)
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@gmail(\.com)?")
RESULT_CHAR_LIMIT = 20000


def scrub(text: str) -> str:
    text = SYSTEM_REMINDER.sub("[system-reminder omitted — private user configuration]", text)
    text = LOCAL_CAVEAT.sub("", text)
    return EMAIL.sub("[email redacted]", text)


def fence(text: str, lang: str = "") -> str:
    tick = "````" if "```" in text else "```"
    return f"{tick}{lang}\n{text.rstrip()}\n{tick}\n"


def timestamp(entry: dict) -> str:
    raw = entry.get("timestamp")
    if not raw:
        return ""
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).strftime("%H:%M:%S")
    except ValueError:
        return ""


def render_tool_use(block: dict, out: list[str], tool_names: dict[str, str]) -> None:
    tool_names[block["id"]] = block["name"]
    params = block.get("input", {})
    if block["name"] == "Bash" and "command" in params:
        out.append(f"**Tool: Bash** — {params.get('description', '')}\n" + fence(scrub(params["command"]), "bash"))
        return
    out.append(f"**Tool: {block['name']}**\n" + fence(scrub(json.dumps(params, indent=2, ensure_ascii=False)), "json"))


def render_tool_result(block: dict, out: list[str], tool_names: dict[str, str]) -> None:
    name = tool_names.get(block.get("tool_use_id"), "tool")
    content = block.get("content")
    parts: list[str] = []
    if isinstance(content, str):
        parts.append(scrub(content))
    elif isinstance(content, list):
        for part in content:
            if part.get("type") == "text":
                parts.append(scrub(part["text"]))
            elif part.get("type") == "image":
                parts.append("[image omitted — see the PNG files in analysis/]")
    body = "\n".join(parts).strip() or "(empty)"
    if len(body) > RESULT_CHAR_LIMIT:
        body = body[:RESULT_CHAR_LIMIT] + f"\n… [truncated: {len(body):,} chars total]"
    out.append(f"<details><summary>Result ({name})</summary>\n\n" + fence(body) + "\n</details>\n")


def render_block(block: dict, out: list[str], tool_names: dict[str, str]) -> None:
    kind = block.get("type")
    if kind == "text":
        out.append(scrub(block["text"]) + "\n")
    elif kind == "thinking":
        text = scrub(block.get("thinking", "")).strip()
        if text:
            out.append("<details><summary>Thinking</summary>\n\n" + fence(text) + "\n</details>\n")
    elif kind == "tool_use":
        render_tool_use(block, out, tool_names)
    elif kind == "tool_result":
        render_tool_result(block, out, tool_names)
    elif kind == "image":
        out.append("[image omitted]\n")


def render_user(entry: dict, out: list[str], tool_names: dict[str, str]) -> bool:
    content = entry.get("message", {}).get("content")
    stamp = timestamp(entry)
    if isinstance(content, str):
        text = scrub(content).strip()
        if not text:
            return False
        out.append(f"\n---\n\n## User  `{stamp}`\n\n{text}\n")
        return True
    has_text = any(b.get("type") == "text" and scrub(b["text"]).strip() for b in content)
    if has_text:
        out.append(f"\n---\n\n## User  `{stamp}`\n")
    for block in content:
        render_block(block, out, tool_names)
    return has_text


def render(path: str, title: str) -> str:
    out = [
        f"# {title}\n",
        f"Source: `{path.split('/')[-1]}` (Claude Code session log). Rendered by `render_transcript.py`; "
        "see README.md in this folder for what was redacted.\n",
    ]
    tool_names: dict[str, str] = {}
    n_user = n_assistant = 0
    for line in open(path):
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        kind = entry.get("type")
        if kind == "user":
            n_user += render_user(entry, out, tool_names)
        elif kind == "assistant":
            n_assistant += 1
            out.append(f"\n### Assistant  `{timestamp(entry)}`\n")
            for block in entry.get("message", {}).get("content") or []:
                render_block(block, out, tool_names)
    out.insert(2, f"\n{n_user} user turns, {n_assistant} assistant turns.\n")
    return "".join(out)


if __name__ == "__main__":
    source, destination, title = sys.argv[1:4]
    with open(destination, "w") as handle:
        handle.write(render(source, title))
    print(destination, "written")
