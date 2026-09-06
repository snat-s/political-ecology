"""Generate opaque identities independently of allocation seeds and indices."""

import hashlib
import secrets


def agent_ids(count: int) -> tuple[str, ...]:
    """Return fresh SHA-256 identities backed by independent random entropy."""
    return tuple(
        hashlib.sha256(secrets.token_bytes(32)).hexdigest()
        for _ in range(count)
    )
