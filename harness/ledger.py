"""Host-side SQLite operations; these functions are not exposed as Pi tools."""

import contextlib
import sqlite3
from pathlib import Path

SCHEMA = Path(__file__).parent / "schema.sql"


@contextlib.contextmanager
def connect(path: Path):
    """Open a ledger connection and always close it after use."""
    database = sqlite3.connect(path, timeout=30)
    database.row_factory = sqlite3.Row
    try:
        yield database
    finally:
        database.close()


def initialize(
    path: Path,
    tokens: tuple[int, ...],
    common_tokens: int,
    agent_ids: tuple[str, ...],
) -> None:
    """Create accounts before starting agents or the environmental timers."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with connect(path) as database, database:
        database.executescript(SCHEMA.read_text())
        database.execute("INSERT INTO pool VALUES (1, ?)", (common_tokens,))
        database.executemany(
            "INSERT INTO agents VALUES (?, ?)",
            list(zip(agent_ids, tokens, strict=True)),
        )


def balance(path: Path, agent_id: str) -> int:
    """Return one agent's committed balance."""
    with connect(path) as database:
        row = database.execute(
            "SELECT balance FROM agents WHERE agent_id = ?",
            (agent_id,),
        ).fetchone()
    if row is None:
        raise ValueError(f"Unknown agent: {agent_id}")
    return row["balance"]


def viable_count(path: Path) -> int:
    """Count agents with positive balances."""
    with connect(path) as database:
        return database.execute(
            "SELECT count(*) FROM agents WHERE balance > 0",
        ).fetchone()[0]


def refill(path: Path, amount: int) -> None:
    """Atomically credit the common pool and record the refill transaction."""
    if type(amount) is not int or amount <= 0:
        raise ValueError("Refill amount must be a positive integer")
    with connect(path) as database, database:
        database.execute("BEGIN IMMEDIATE")
        database.execute(
            "UPDATE pool SET balance = balance + ? WHERE singleton = 1",
            (amount,),
        )
        current = database.execute(
            "SELECT balance FROM pool WHERE singleton = 1",
        ).fetchone()[0]
        database.execute(
            """INSERT INTO transactions
               (kind, actor, destination, amount, destination_balance_after)
               VALUES ('refill', 'environment', 'common-pool', ?, ?)""",
            (amount, current),
        )


def snapshot(path: Path) -> dict:
    """Read balances and transactions from one consistent SQLite snapshot."""
    with connect(path) as database, database:
        database.execute("BEGIN")
        pool = database.execute("SELECT balance FROM pool").fetchone()[0]
        agents = dict(
            database.execute(
                "SELECT agent_id, balance FROM agents ORDER BY agent_id",
            ).fetchall()
        )
        transactions = [
            dict(row)
            for row in database.execute(
                "SELECT * FROM transactions ORDER BY id",
            )
        ]
    return {"common-pool": pool, "agents": agents, "transactions": transactions}
