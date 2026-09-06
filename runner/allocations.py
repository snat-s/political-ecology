#!/usr/bin/env python3
"""Generate reproducible starting balances for experiments A.1 and A.2."""

import argparse
import json
import random

from harness import identities


def allocations(
    experiment: str, count: int, seed: int, equal_tokens: int
) -> list[int]:
    """Sample deterministic initial balances for the requested experiment."""
    if experiment not in {"A.1", "A.2"} or count < 1 or equal_tokens < 0:
        raise ValueError("Invalid experiment, count, or token budget")
    if experiment == "A.1" or equal_tokens == 0:
        return [equal_tokens] * count

    rng = random.Random(seed)
    # Preserve the A.2 unequal distribution at the requested trial scale.
    mean = equal_tokens
    sigma = max(1, round(equal_tokens * 0.30))
    # Three standard deviations around the mean: 0.1x to 1.9x at the
    # default 30%-of-mean sigma.
    lower = max(1, round(equal_tokens * 0.10))
    upper = round(equal_tokens * 1.90)
    values: list[int] = []
    while len(values) < count:
        value = round(rng.gauss(mean, sigma))
        if lower <= value <= upper:
            values.append(value)
    return values


def main() -> None:
    """Print initial balances as JSON or comma-separated values."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment", choices=("A.1", "A.2"), required=True)
    parser.add_argument("--count", type=int, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--equal-tokens", type=int, default=100_000)
    parser.add_argument("--format", choices=("csv", "json"), default="json")
    args = parser.parse_args()
    if args.count < 1 or args.equal_tokens < 0:
        parser.error("--count must be positive and --equal-tokens nonnegative")
    values = allocations(
        args.experiment, args.count, args.seed, args.equal_tokens
    )
    if args.format == "csv":
        print(",".join(map(str, values)))
        return
    print(
        json.dumps(
            {
                "experiment": args.experiment,
                "seed": args.seed,
                "distribution": (
                    {"kind": "equal", "value": args.equal_tokens}
                    if args.experiment == "A.1"
                    else {
                        "kind": "truncated_normal",
                        "mu": args.equal_tokens,
                        "sigma": round(args.equal_tokens * 0.30),
                        "bounds": [
                            max(1, round(args.equal_tokens * 0.10)),
                            round(args.equal_tokens * 1.90),
                        ],
                    }
                ),
                "agents": dict(
                    zip(identities.agent_ids(len(values)), values, strict=True)
                ),
            },
        )
    )


if __name__ == "__main__":
    main()
