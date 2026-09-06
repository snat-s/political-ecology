"""Protect failure reporting while the launcher is reorganized."""

import json

import pytest

from harness.config import Config
from runner import report
from runner.artifacts import finish_run, has_provider_error, prepare_run


def test_provider_error_is_not_hidden_by_successful_process(tmp_path):
    event = {"type": "message_end", "message": {"stopReason": "error"}}
    (tmp_path / "fleet.log").write_text(
        "startup text\n[pi-0] {incomplete\n" + "[pi-0] " + json.dumps(event)
    )
    assert has_provider_error(tmp_path)


def test_normal_output_does_not_count_as_provider_failure(tmp_path):
    (tmp_path / "fleet.log").write_text(
        '[pi-0] {"message": {"stopReason": "stop"}}\n'
    )
    assert not has_provider_error(tmp_path)


@pytest.mark.parametrize(
    "status,state", [(0, "completed"), (1, "failed"), (124, "timed_out")]
)
def test_outcome_is_saved_even_before_logs_exist(tmp_path, status, state):
    finish_run(tmp_path, {"model": "test/model"}, status)
    summary = json.loads((tmp_path / "summary.json").read_text())
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert summary["state"] == manifest["state"] == state
    assert summary["exit_status"] == status


def test_completed_run_builds_report_from_fleet_log(tmp_path):
    (tmp_path / "allocations.json").write_text(
        json.dumps({"agents": {"agent-0": 128}})
    )
    (tmp_path / "fleet.log").write_text(
        "[pi-0] AGENT_BEGIN\n"
        "[pi-0] AGENT_END status=0 turns=1 balance=64\n"
        'FINAL_LEDGER {"agents": []}\n'
    )
    finish_run(tmp_path, {"model": "test/model"}, 0)
    assert "AGENT_END" in (tmp_path / "agents/pi-00.log").read_text()
    assert json.loads((tmp_path / "final-ledger.json").read_text()) == {
        "agents": []
    }
    assert "Agent ended" in (tmp_path / "transcript.html").read_text()


def test_run_ids_survive_config_ledger_and_report(tmp_path, monkeypatch):
    from types import SimpleNamespace

    from harness import ledger

    monkeypatch.setattr("runner.artifacts.ROOT", tmp_path)
    args = SimpleNamespace(
        model="test/model", reasoning="off", pool=50, max_turns=2
    )
    run_dir = prepare_run(args, [10, 20], {"model": args.model})
    settings = Config.load(run_dir / "config.json")
    allocations = json.loads((run_dir / "allocations.json").read_text())[
        "agents"
    ]
    assert list(allocations) == list(settings.agent_ids)
    ledger_path = tmp_path / "ledger.sqlite"
    ledger.initialize(
        ledger_path, settings.tokens, settings.common_tokens, settings.agent_ids
    )
    assert ledger.snapshot(ledger_path)["agents"] == allocations
    (run_dir / "fleet.log").write_text(
        "[pi-1] AGENT_END status=0 turns=1 balance=20\n"
    )
    parsed = report.parse_run(run_dir)
    assert parsed["agents"] == list(settings.agent_ids)
    assert parsed["events"][0]["agent"] == settings.agent_ids[1]
