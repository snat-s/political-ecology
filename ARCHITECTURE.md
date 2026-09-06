# Read the code in one sitting

The experiment has three layers. Read their entry points first, then open only
the policy you want to change. There is no plugin discovery or backend framework.

## 1. Launch a sandbox

Start with **`run.py`**. It resolves options, prepares a run, calls one backend,
and saves the outcome even if execution fails.

- `runner/config.py` resolves CLI options against `models.json`.
- `runner/backends.py` contains the two concrete implementations: local and Modal.
- `runner/artifacts.py` writes metadata, detects provider errors, and builds reports.

Both backends run the same Dockerfile and `harness/fleet.py`. Only the selected
provider credential enters the sandbox. It is never part of the run configuration.

## 2. Run the fleet

Read **`harness/fleet.py`**. It starts the refill timer, starts the agents, watches
for a single survivor, waits for completion, and prints the final ledger.

**`harness/agent.py`** is one agent's lifecycle: prepare its prompt and explicit Pi
command, run budgeted turns, wait for every peer, and produce a final reflection.
`config.py` loads their shared JSON settings into a dataclass. `ledger.py` uses
Python’s SQLite library for balance inspection, refills, and the final snapshot.
`schema.sql` is shared with the TypeScript extension.

Python task groups manage the Pi child processes and the reflection barrier.
Cancellation terminates and reaps children. No shell is used to launch agents or
parse configuration.

## 3. Apply the experiment rules

Read **`harness/extensions/token-economy.ts`**. This is the sole extension entry
point passed to Pi. It installs tool guards and three groups of behavior:

- `budget.ts`: reserve output tokens before a request and charge actual usage.
- `files.ts`: workspace directory listing and ordinary file reads/writes.
- `ledger.ts`: the `count_tokens` / `get_tokens` tools on the fleet-initialized ledger.

All balance mutations use SQLite transactions. Agents cannot access the ledger
through their file tools. A token reservation limits output but does not protect
an account from peer withdrawals. Final reflections disable every tool and token
charge; the fleet stops refills before reflections begin.

## Boundaries to preserve

A fleet shares one sandbox and one SQLite database. Splitting agents across
sandboxes would change the experiment's coordination and storage model.

`--max-turns` bounds Pi invocations. The timeout bounds elapsed execution.
Neither is a dollar budget, and final reflections are outside token accounting.

`runner/allocations.py` generates starting balances. `runner/report.py` builds
reports using `runner/templates/transcript.html`, the standalone report UI.
Previous results and narrative reports are not application source.

## Before finishing a change

```bash
uv run ruff check run.py runner harness tests
uv run ruff format --check run.py runner harness tests
uv run python -m pytest -q
npm run check
```

For lifecycle or extension changes, also run a small local experiment. Test Modal
when changing cloud lifecycle or file-transfer behavior. Keep entry points short,
use names that describe the experiment, and avoid introducing generic machinery
for only two backends and five tools.
