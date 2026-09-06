#!/usr/bin/env python3
"""Turn a fleet fleet.log into a standalone chronological chat transcript."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

MARKER = re.compile(r"^\[pi-(\d+)\] (.*)$")
CONTINUE = re.compile(r"AGENT_AUTOCONTINUE turn=(\d+) balance=(\d+)")
END = re.compile(r"AGENT_END status=(\d+) turns=(\d+) balance=(\d*)")


def blocks(items, kind="text"):
    """Join text or thinking blocks from a Pi message."""
    key = "thinking" if kind == "thinking" else "text"
    return "\n".join(
        str(x.get(key, ""))
        for x in items
        if x.get("type") == kind and x.get(key)
    )


def parse_run(run_dir: Path):
    """Parse a saved fleet stream into ordered report events."""
    manifest = json.loads((run_dir / "manifest.json").read_text())
    allocations = json.loads((run_dir / "allocations.json").read_text())
    initial = allocations["agents"]
    # Allocation order maps host-only pi-N log labels to opaque account IDs.
    agents = list(initial)
    if all(re.fullmatch(r"agent-\d+", identity) for identity in agents):
        agents.sort(key=lambda identity: int(identity.rsplit("-", 1)[-1]))
    events, pending, seq, final_phase = [], {}, 0, set()
    turns = {agent: 1 for agent in initial}

    def add(time, agent, kind, **rest):
        nonlocal seq
        seq += 1
        item = dict(
            time=time,
            agent=agent,
            turn=turns.get(agent, 1),
            kind=kind,
            sequence=seq,
            **rest,
        )
        events.append(item)
        return item

    for raw in (run_dir / "fleet.log").open(errors="replace"):
        m = MARKER.search(raw)
        if not m:
            continue
        time, agent, payload = (
            float(seq),
            agents[int(m.group(1))],
            m.group(2).strip(),
        )
        if payload == "AGENT_FINAL_MESSAGE_BEGIN":
            final_phase.add(agent)
            add(
                time,
                agent,
                "system",
                title="Final reflection",
                text="Unmetered text-only reflection begins; tools are disabled",
            )
            continue
        if payload == "AGENT_FINAL_MESSAGE_END":
            final_phase.discard(agent)
            continue
        if x := CONTINUE.search(payload):
            turns[agent] = int(x.group(1))
            add(
                time,
                agent,
                "system",
                title=f"Turn {x.group(1)}",
                text=f"Balance: {int(x.group(2)):,} tokens",
            )
            continue
        if x := END.search(payload):
            add(
                time,
                agent,
                "system",
                title="Agent ended",
                text=f"Status {x.group(1)} · {x.group(2)} turns · {int(x.group(3) or 0):,} tokens",
            )
            continue
        if not payload.startswith("{"):
            continue
        try:
            event = json.loads(payload)
        except json.JSONDecodeError:
            continue
        kind = event.get("type")
        if kind == "message_end":
            msg = event.get("message", {})
            if msg.get("role") == "assistant":
                text, thinking = (
                    blocks(msg.get("content", [])),
                    blocks(msg.get("content", []), "thinking"),
                )
                if text or thinking:
                    add(
                        time,
                        agent,
                        "message",
                        text=text,
                        thinking=thinking,
                        final=agent in final_phase,
                        stop=msg.get("stopReason", ""),
                        usage=msg.get("usage", {}),
                    )
        elif kind == "tool_execution_start":
            cid = str(event.get("toolCallId", ""))
            pending[cid] = add(
                time,
                agent,
                "tool",
                tool=event.get("toolName", "unknown"),
                args=event.get("args", {}),
                callId=cid,
                final=agent in final_phase,
                result=None,
                error=False,
            )
        elif kind == "tool_execution_end":
            cid, result = (
                str(event.get("toolCallId", "")),
                event.get("result", {}),
            )
            if item := pending.pop(cid, None):
                item.update(
                    result=blocks(result.get("content", [])),
                    details=result.get("details", {}),
                    error=bool(result.get("isError") or event.get("isError")),
                    endTime=time,
                )
    events.sort(key=lambda e: (e["time"], e["sequence"]))
    shared = ""
    for event in events:
        if (
            event["kind"] != "tool"
            or event.get("tool") != "write"
            or event.get("error")
        ):
            continue
        path = str(event.get("args", {}).get("path", ""))
        if Path(path).name != "shared.txt":
            continue
        content = str(event.get("args", {}).get("content", ""))
        public = (
            content.replace(shared, "", 1).strip()
            if shared and shared in content
            else content.strip()
        )
        event["public"] = (
            public or "(rewrote the shared file without adding text)"
        )
        event["preserved"] = bool(shared and shared in content)
        shared = content
    return dict(
        run=run_dir.name,
        manifest=manifest,
        initial=initial,
        agents=agents,
        events=events,
    )


def render_report(data):
    """Embed parsed events in the standalone report template."""
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    template = (Path(__file__).parent / "templates/transcript.html").read_text()
    return template.replace("__DATA__", payload)


def main():
    """Render a saved run as a standalone HTML transcript."""
    p = argparse.ArgumentParser()
    p.add_argument("run_dir", type=Path)
    p.add_argument("--output", type=Path)
    a = p.parse_args()
    out = a.output or a.run_dir / "transcript.html"
    out.write_text(render_report(parse_run(a.run_dir)))
    print(out)


if __name__ == "__main__":
    main()
