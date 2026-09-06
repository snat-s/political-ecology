"""Verify fleet lifecycle boundaries without making provider requests."""

import asyncio
import dataclasses
from pathlib import Path

import pytest

from harness import agent, config, fleet, ledger


@pytest.fixture
def settings(tmp_path):
    return config.Config(
        model="test/model",
        reasoning="off",
        tokens=(10, 10),
        common_tokens=0,
        max_turns=2,
        root=tmp_path,
        source=Path(__file__).resolve().parents[1],
    )


def test_reflections_wait_for_every_budgeted_agent(settings, monkeypatch):
    completed = set()
    reflected = set()

    async def invoke(member, prompt, *, first=False, final=False):
        if final:
            assert completed == {0, 1}
            reflected.add(member.index)
        else:
            await asyncio.sleep(0.01 * member.index)
            if member.turns == 2:
                completed.add(member.index)
        return 0

    monkeypatch.setattr(agent.Agent, "invoke", invoke)
    assert asyncio.run(fleet.run(settings)) == 0
    assert reflected == {0, 1}
    assert ledger.snapshot(settings.ledger_path)["transactions"] == []


def test_agent_failure_cannot_deadlock_reflection_barrier(
    settings, monkeypatch
):
    reflected = set()

    async def invoke(member, prompt, *, first=False, final=False):
        if final:
            reflected.add(member.index)
            return 0
        return 1 if member.index == 0 else 0

    monkeypatch.setattr(agent.Agent, "invoke", invoke)
    assert asyncio.run(fleet.run(settings)) == 1
    assert reflected == {0, 1}


def test_cancelled_pi_process_is_reaped(settings, tmp_path):
    # Use an actual child process to check the cancellation cleanup path.
    script = tmp_path / "waiting.mjs"
    script.write_text("console.log('READY'); setInterval(() => {}, 1000);")
    settings = dataclasses.replace(settings, pi_cli=str(script))
    (settings.root / "agents" / settings.agent_ids[0]).mkdir(parents=True)
    member = agent.Agent(settings, 0)
    ready = asyncio.Event()
    member.log = lambda message: ready.set() if message == "READY" else None

    async def exercise():
        task = asyncio.create_task(member.invoke("test", first=True))
        await asyncio.wait_for(ready.wait(), timeout=5)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await asyncio.wait_for(task, timeout=6)

    asyncio.run(exercise())


def test_configuration_loads_json_without_shell_evaluation(tmp_path):
    import json

    path = tmp_path / "config.json"
    path.write_text(
        json.dumps(
            {
                "model": "test/model",
                "reasoning": "off",
                "tokens": [10, 20],
                "common_tokens": 30,
                "max_turns": 4,
            }
        )
    )
    loaded = config.Config.load(path)
    assert loaded.tokens == (10, 20)
    assert loaded.common_tokens == 30
    assert loaded.max_turns == 4


def test_agent_identities_are_opaque_and_stable_within_run(settings):
    import re

    assert len(set(settings.agent_ids)) == len(settings.tokens)
    assert all(
        re.fullmatch(r"[0-9a-f]{64}", identity)
        for identity in settings.agent_ids
    )
    assert agent.Agent(settings, 0).identity == settings.agent_ids[0]
    assert (
        dataclasses.replace(settings, agent_ids=()).agent_ids
        != settings.agent_ids
    )
    environment = agent.Agent(settings, 0).environment(False)
    assert environment["POLITICAL_ECOLOGY_AGENT_ID"] == settings.agent_ids[0]
    assert settings.agent_ids[1] not in " ".join(environment.values())


@pytest.mark.parametrize(
    "ids", [("a" * 64,), ("a" * 64, "a" * 64), ("agent-0", "agent-1")]
)
def test_invalid_identity_mappings_are_rejected(settings, ids):
    with pytest.raises(ValueError):
        dataclasses.replace(settings, agent_ids=ids)
