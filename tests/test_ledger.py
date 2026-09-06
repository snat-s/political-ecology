"""Exercise Python ledger operations against the shared SQLite schema."""

import sqlite3

import pytest

from harness import ledger


@pytest.fixture
def ledger_path(tmp_path):
    path = tmp_path / "economy.sqlite"
    ledger.initialize(path, (10, 20), 50, ("a" * 64, "b" * 64))
    return path


def test_refill_changes_balance_and_records_transaction(ledger_path):
    ledger.refill(ledger_path, 25)
    saved = ledger.snapshot(ledger_path)
    assert saved["common-pool"] == 75
    assert saved["agents"] == {"a" * 64: 10, "b" * 64: 20}
    transaction = saved["transactions"][0]
    assert transaction["kind"] == "refill"
    assert transaction["amount"] == 25
    assert transaction["destination_balance_after"] == 75


@pytest.mark.parametrize("amount", [-1, 0, 1.5, "invalid", True])
def test_invalid_refill_leaves_ledger_unchanged(ledger_path, amount):
    before = ledger.snapshot(ledger_path)
    with pytest.raises(ValueError):
        ledger.refill(ledger_path, amount)
    assert ledger.snapshot(ledger_path) == before


def test_balances_and_survivors(ledger_path):
    assert ledger.balance(ledger_path, "a" * 64) == 10
    assert ledger.viable_count(ledger_path) == 2
    with sqlite3.connect(ledger_path) as database:
        database.execute(
            "UPDATE agents SET balance = 0 WHERE agent_id = ?", ("a" * 64,)
        )
    assert ledger.viable_count(ledger_path) == 1
    with pytest.raises(ValueError, match="Unknown agent"):
        ledger.balance(ledger_path, "missing")
