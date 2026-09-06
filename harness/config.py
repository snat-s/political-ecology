"""Load the explicit, non-secret fleet configuration."""

import dataclasses
import json
import os
from pathlib import Path

from harness import identities


@dataclasses.dataclass(frozen=True)
class Config:
    """Settings shared by all agents in one sandbox."""

    model: str
    reasoning: str
    tokens: tuple[int, ...]
    common_tokens: int
    max_turns: int
    agent_ids: tuple[str, ...] = ()
    root: Path = Path("/experiment")
    source: Path = Path("/opt/experiment")
    pi_cli: str = "/usr/local/lib/node_modules/@earendil-works/pi-coding-agent/dist/bundle/cli.js"

    def __post_init__(self):
        """Create identities once and reject ambiguous account mappings."""
        if not self.agent_ids:
            object.__setattr__(
                self, "agent_ids", identities.agent_ids(len(self.tokens))
            )
        if len(self.agent_ids) != len(self.tokens) or len(
            set(self.agent_ids)
        ) != len(self.tokens):
            raise ValueError("Each token allocation requires a unique agent ID")
        if any(
            len(identity) != 64
            or any(c not in "0123456789abcdef" for c in identity)
            for identity in self.agent_ids
        ):
            raise ValueError("Agent IDs must be lowercase SHA-256 hex digests")

    @property
    def ledger_path(self) -> Path:
        """Return the shared ledger path outside the agents' file workspace."""
        return self.root / "state/economy.sqlite"

    @classmethod
    def load(cls, path: Path) -> "Config":
        """Read the JSON configuration written by the host launcher."""
        data = json.loads(path.read_text())
        return cls(
            model=data["model"],
            reasoning=data["reasoning"],
            tokens=tuple(data["tokens"]),
            common_tokens=data["common_tokens"],
            max_turns=data["max_turns"],
            agent_ids=tuple(data.get("agent_ids", ())),
            pi_cli=os.environ.get("PI_CLI", cls.pi_cli),
        )
