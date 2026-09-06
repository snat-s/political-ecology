"""Resolve CLI options and model presets without starting a run."""

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def parse_args():
    """Parse explicit runtime and experiment settings."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--backend", choices=["local", "modal"], default="local"
    )
    parser.add_argument(
        "--model", default="mini", help="Preset or provider/model"
    )
    parser.add_argument(
        "--key-env", help="Credential variable for a custom model"
    )
    parser.add_argument(
        "--api-domain", action="append", help="Allowed API domain (repeatable)"
    )
    parser.add_argument(
        "--reasoning",
        choices=["off", "minimal", "low", "medium", "high", "xhigh", "max"],
    )
    parser.add_argument("--agents", type=int, default=2)
    parser.add_argument("--tokens", type=int, default=500)
    parser.add_argument("--pool", type=int, default=0)
    parser.add_argument("--experiment", choices=["A.1", "A.2"], default="A.1")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--max-turns", type=int, default=3)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--engine", choices=["docker", "podman"])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if (
        not 1 <= args.agents <= 100
        or min(args.tokens, args.pool, args.seed) < 0
    ):
        parser.error(
            "agents must be 1–100; budgets and seed must be nonnegative"
        )
    if args.max_turns < 1 or not 1 <= args.timeout <= 86400:
        parser.error(
            "max-turns must be positive; timeout must be 1–86400 seconds"
        )
    presets = json.loads((ROOT / "models.json").read_text())
    preset = presets.get(args.model, {})
    args.model = preset.get("model", args.model)
    args.key_env = args.key_env or preset.get("key_env")
    args.api_domain = args.api_domain or preset.get("domains")
    args.reasoning = args.reasoning or preset.get("reasoning", "off")
    if "/" not in args.model or not args.key_env or not args.api_domain:
        parser.error(
            "custom models require provider/model, --key-env, and --api-domain"
        )
    return args
