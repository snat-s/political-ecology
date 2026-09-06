"""Coordinate budgeted agents, environmental supply, and final reflections."""

import asyncio
import json
import signal
from pathlib import Path

from harness import agent, config, ledger


async def refill_pool(settings: config.Config) -> None:
    """Apply the original wall-clock refill schedule until cancelled."""
    delay, amount = 60, 1000
    while True:
        await asyncio.sleep(delay)
        ledger.refill(settings.ledger_path, amount)
        print(f"POOL_REFILL amount={amount}", flush=True)
        delay, amount = (240, 2000) if delay == 60 else (300, 1000)


async def monitor_survivors(
    settings: config.Config, stop: asyncio.Event
) -> None:
    """Ask agents to stop between turns when one positive balance remains."""
    while not stop.is_set():
        count = ledger.viable_count(settings.ledger_path)
        if count == 1:
            print("SINGLETON_STOP viable_agents=1", flush=True)
            stop.set()
            return
        await asyncio.sleep(2)


async def run(settings: config.Config) -> int:
    """Finish every budgeted phase before freezing supply and reflecting."""
    (settings.root / "shared").mkdir(parents=True, exist_ok=True)
    ledger.initialize(
        settings.ledger_path,
        settings.tokens,
        settings.common_tokens,
        settings.agent_ids,
    )
    agents = [
        agent.Agent(settings, index) for index in range(len(settings.tokens))
    ]
    stop = asyncio.Event()
    async with asyncio.TaskGroup() as background:
        refill = background.create_task(refill_pool(settings))
        monitor = background.create_task(monitor_survivors(settings, stop))
        async with asyncio.TaskGroup() as budgeted:
            for member in agents:
                budgeted.create_task(member.run_budget(stop))
        # Cancelling timers here is the barrier: no refill can reach reflections.
        refill.cancel()
        monitor.cancel()
    async with asyncio.TaskGroup() as reflections:
        for member in agents:
            reflections.create_task(member.reflect())
    print(
        "FINAL_LEDGER " + json.dumps(ledger.snapshot(settings.ledger_path)),
        flush=True,
    )
    status = int(any(member.status for member in agents))
    print(f"PI_FLEET_END status={status}", flush=True)
    return status


async def main() -> int:
    """Load the run configuration and cancel Pi children on termination."""
    settings = config.Config.load(Path("/experiment/config.json"))
    task = asyncio.create_task(run(settings))
    loop = asyncio.get_running_loop()
    for signum in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(signum, task.cancel)
    try:
        return await task
    except asyncio.CancelledError:
        return 124


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
