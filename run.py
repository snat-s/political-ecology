#!/usr/bin/env python3
"""Run the same Pi fleet in a local container or a Modal sandbox."""

import json
import os

import dotenv

from runner import allocations, artifacts, backends, config


def main() -> int:
    """Validate configuration, execute a fleet, and record its outcome."""
    args = config.parse_args()
    values = allocations.allocations(
        args.experiment, args.agents, args.seed, args.tokens
    )
    manifest = {
        **vars(args),
        "schema_version": 2,
        "runtime": args.backend,
        "agent_count": args.agents,
        "common_pool_initial": args.pool,
        "state": "running",
    }
    if args.dry_run:
        print(json.dumps({**manifest, "allocations": values}, indent=2))
        return 0
    key = os.environ.get(args.key_env) or dotenv.dotenv_values(
        config.ROOT / ".env.local"
    ).get(args.key_env)
    if not key:
        raise RuntimeError(
            f"Missing {args.key_env} in environment or .env.local"
        )
    run_dir = artifacts.prepare_run(args, values, manifest)
    print(f"Artifacts: {run_dir}", flush=True)
    status = 1
    try:
        runner = (
            backends.run_modal
            if args.backend == "modal"
            else backends.run_local
        )
        status = runner(args, run_dir, {args.key_env: key})
        if status == 0 and artifacts.has_provider_error(run_dir):
            status = 1
    finally:
        artifacts.finish_run(run_dir, manifest, status)
    return status


if __name__ == "__main__":
    raise SystemExit(main())
