"""Write run metadata and extract human-readable transcripts."""

import json
import os
import re
import time

from harness import identities
from runner import report
from runner.config import ROOT


def collect_transcripts(run_dir):
    """Extract individual transcripts and the ledger from the fleet stream."""
    streams = {}
    for line in (
        (run_dir / "fleet.log").read_text(errors="replace").splitlines()
    ):
        match = re.search(r"\[pi-(\d+)\] (.*)", line)
        if match:
            streams.setdefault(int(match[1]), []).append(match[2])
        if line.startswith("FINAL_LEDGER "):
            (run_dir / "final-ledger.json").write_text(
                line.removeprefix("FINAL_LEDGER ")
            )
    (run_dir / "agents").mkdir(exist_ok=True)
    for index, lines in streams.items():
        (run_dir / "agents" / f"pi-{index:02d}.log").write_text(
            "\n".join(lines) + "\n"
        )
    (run_dir / "transcript.html").write_text(
        report.render_report(report.parse_run(run_dir))
    )


def prepare_run(args, values, manifest):
    """Create the run directory and its non-secret input files."""
    agent_ids = identities.agent_ids(len(values))
    run_dir = (
        ROOT
        / "logs/runs"
        / f"{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}-{os.getpid()}"
    )
    run_dir.mkdir(parents=True)
    (run_dir.parent / "latest").write_text(str(run_dir) + "\n")
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    (run_dir / "allocations.json").write_text(
        json.dumps({"agents": dict(zip(agent_ids, values, strict=True))})
    )
    settings = {
        "model": args.model,
        "reasoning": args.reasoning,
        "tokens": values,
        "agent_ids": agent_ids,
        "common_tokens": args.pool,
        "max_turns": args.max_turns,
    }
    (run_dir / "config.json").write_text(json.dumps(settings, indent=2))
    return run_dir


def finish_run(run_dir, manifest, status):
    """Record the outcome and collect any available logs."""
    state = {0: "completed", 124: "timed_out"}.get(status, "failed")
    (run_dir / "summary.json").write_text(
        json.dumps(
            {**manifest, "state": state, "exit_status": status}, indent=2
        )
    )
    (run_dir / "manifest.json").write_text(
        json.dumps({**manifest, "state": state}, indent=2)
    )
    if (run_dir / "fleet.log").exists():
        collect_transcripts(run_dir)


def has_provider_error(run_dir):
    """Detect API failures that Pi may report with a successful exit code."""
    for line in (
        (run_dir / "fleet.log").read_text(errors="replace").splitlines()
    ):
        match = re.search(r"\[pi-\d+\] (\{.*)", line)
        if not match:
            continue
        try:
            event = json.loads(match[1])
        except json.JSONDecodeError:
            continue
        if event.get("message", {}).get("stopReason") == "error":
            return True
    return False
