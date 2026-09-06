# Political ecology of agent systems

Run a fleet of Pi agents with five explicit tools (`ls`, `read`, `write`,
`count_tokens`, and `get_tokens`) and a shared SQLite token economy.

## Quick start

Install [uv](https://docs.astral.sh/uv/). For local sandboxes, install Docker or
Podman. For cloud sandboxes, authenticate Modal once:

```bash
uv sync
uv run modal setup
```

Put your provider credential in `.env.local`, or export it in your shell. Only
the credential selected for a run is passed to the container; `.env.local` is
never copied into an image or run artifact.

```bash
# Small local experiment (Docker or Podman).
uv run run.py --backend local --model mini

# The same experiment in a Modal sandbox; no local container engine required.
uv run run.py --backend modal --model mini

# Inspect resolved settings without credentials, cloud resources, or API calls.
uv run run.py --backend modal --model luna --dry-run
```

The defaults are two agents, 500 output tokens each, no initial common pool,
three continuation turns, and a 180-second runtime limit. Final reflections are
unmetered by the economy and still incur provider usage. The timeout includes
reflections but excludes image construction. One sandbox contains the whole
fleet so SQLite transactions and workspace files retain their original
semantics. Sandboxes are terminated after artifacts are downloaded.

## Models and experiments

`models.json` lists explicit presets: provider/model ID, credential environment
variable, allowed API domains, and reasoning level. `mini` uses
`openai/gpt-4.1-mini`. Other presets require account access to their model and
the corresponding credential. Change any preset or pass a Pi-supported model:

```bash
uv run run.py --backend modal --model deepseek
uv run run.py --backend modal --model openai/gpt-4.1-mini \
  --key-env OPENAI_API_KEY --api-domain api.openai.com --reasoning off
uv run run.py --backend modal --model mini --experiment A.2 --seed 7 \
  --agents 10 --tokens 2000 --pool 10000 --max-turns 100 --timeout 1800
```

Each run generates fresh SHA-256 agent IDs from random entropy, independent of
the allocation seed. IDs are saved in `config.json` and `allocations.json`;
sequential `pi-N` labels are only used in host logs. Agents receive their own ID,
not a roster of peers.

A.1 gives agents equal starting balances. A.2 samples a seeded truncated normal
with mean equal to `--tokens`, standard deviation 30%, and bounds 10–190%.
The environment refills the pool with 1,000 tokens after 60 seconds, 2,000 after
300 seconds, and 1,000 every 300 seconds thereafter. Agents stop on exhausted
budgets, failures, stalls, the turn limit, or when only one viable agent remains.
After all budgeted agents finish, refills stop and text-only reflections begin.
A hard timeout can interrupt this phase; such a run is recorded as timed out.

`--max-turns` limits Pi invocations, not the number of tool calls within one
invocation. Token balances govern output tokens; they do not cap input charges
or constitute a dollar spending limit.

## Explicit harness

Read [ARCHITECTURE.md](ARCHITECTURE.md) for a short guided tour of the code.

- `run.py`: main workflow; `runner/` holds configuration, backends, and artifacts.
- `Dockerfile`: pinned Node and Pi runtime shared by both backends.
- `harness/fleet.py`: fleet coordination; `agent.py` runs each agent lifecycle.
- `harness/extensions/token-economy.ts`: explicit registration of tools and accounting.
- `INSTRUCTIONS.md`: per-agent prompt template.
- `models.json`: provider configuration.
- `harness/config.py`: typed configuration loaded from the run’s `config.json`.
- `harness/ledger.py` and `schema.sql`: host ledger operations and the shared schema.
- `runner/allocations.py` and `runner/report.py`: token allocation and reports.

Pi receives `--no-context-files`, `--no-skills`, `--no-prompt-templates`,
`--no-extensions`, and `--no-builtin-tools`, followed by the explicit extension
path. No hidden extension discovery is used. Agents' file tools are confined to
`/experiment/shared`; the ledger and credentials are outside that directory.
Agents are prompted to read the main local directory (`.`). The `ls` tool lists
that directory by default. Files are created by agents. Writes replace file contents without adding author or timestamp labels.

Modal enforces the selected API-domain egress allowlist. Local containers use
ordinary container networking and do not enforce that domain allowlist. They
have dropped capabilities, no added privileges, and CPU/memory limits. Only the
run output directory is mounted, not your checkout or home directory.

## Artifacts

Each invocation prints its directory under `logs/runs/`; `logs/runs/latest`
contains the latest path. Inspect `manifest.json`, `summary.json`, `fleet.log`,
`agents/pi-*.log`, `final-ledger.json`, and `transcript.html`. Modal also downloads
the board and SQLite ledger and records `sandbox-id.txt`. Failed or timed-out
runs can have partial artifacts. `stderr.log` contains cloud process diagnostics.

```bash
uv run python -m runner.report /path/to/run
```

## Development

Use Google-style Python naming, four-space indentation, explicit imports, and
Google docstrings. TypeScript uses two spaces, single quotes, semicolons, and
80-column formatting. The same two-space convention applies to HTML.
`.editorconfig` records indentation; Ruff enforces Google docstring conventions.
Generated images, vendored runtimes, and experiment
results are excluded from source formatting.

```bash
uv sync
uv run ruff check run.py runner harness tests
uv run ruff format --check run.py runner harness tests
uv run python -m pytest -q
npm ci
npm run check
```

Use `uv run ruff format run.py runner harness tests` and `npm run format` to format sources.
