/** Reserve output budgets before provider requests and settle actual usage. */
import type {ExtensionAPI} from '@earendil-works/pi-coding-agent';
import {agentId, openLedger} from './ledger.ts';

export function registerBudgetAccounting(pi: ExtensionAPI) {
  // Token budgets govern generated (output) tokens. Before every provider call,
  // snapshot the agent's balance and clamp the provider output limit to it.
  // Reservations do not shield balances from peer withdrawals: a concurrent
  // theft can still win, and message_end charges only what remains.
  pi.on('before_provider_request', (event, ctx) => {
    if (process.env.POLITICAL_ECOLOGY_FINAL_MESSAGE === '1')
      return event.payload;
    const id = agentId();
    const db = openLedger();
    let reserved = 0;
    try {
      db.exec('BEGIN IMMEDIATE');
      const existing = db
        .prepare('SELECT amount FROM reservations WHERE agent_id = ?')
        .get(id) as {amount: number} | undefined;
      if (existing)
        throw new Error(`Agent ${id} already has an active token reservation`);
      const row = db
        .prepare('SELECT balance FROM agents WHERE agent_id = ?')
        .get(id) as {balance: number} | undefined;
      if (!row) throw new Error(`Unknown agent account: ${id}`);
      reserved = row.balance;
      const minimumOutput =
        typeof event.payload === 'object' &&
        event.payload !== null &&
        'max_output_tokens' in event.payload
          ? 16
          : 1;
      if (reserved < minimumOutput) {
        db.exec('ROLLBACK');
        ctx.abort();
        return event.payload;
      }
      db.prepare(
        'INSERT INTO reservations(agent_id, amount) VALUES (?, ?)',
      ).run(id, reserved);
      db.exec('COMMIT');
    } catch (error) {
      try {
        db.exec('ROLLBACK');
      } catch {
        /* transaction did not start */
      }
      ctx.abort();
      return event.payload;
    } finally {
      db.close();
    }

    if (
      typeof event.payload !== 'object' ||
      event.payload === null ||
      Array.isArray(event.payload)
    ) {
      ctx.abort();
      return event.payload;
    }
    const payload = {...(event.payload as Record<string, unknown>)};
    if ('max_output_tokens' in payload) {
      payload.max_output_tokens = Math.min(
        Number(payload.max_output_tokens) || reserved,
        reserved,
      );
    } else {
      payload.max_tokens = Math.min(
        Number(payload.max_tokens) || reserved,
        reserved,
      );
    }
    return payload;
  });

  pi.on('message_end', event => {
    const message = event.message as any;
    if (message?.role !== 'assistant') return;
    if (process.env.POLITICAL_ECOLOGY_FINAL_MESSAGE === '1') return;
    const id = agentId();
    const used = Math.max(0, Math.floor(Number(message?.usage?.output) || 0));
    const db = openLedger();
    try {
      db.exec('BEGIN IMMEDIATE');
      const row = db
        .prepare('SELECT amount FROM reservations WHERE agent_id = ?')
        .get(id) as {amount: number} | undefined;
      if (!row) {
        db.exec('COMMIT');
        return;
      }
      const current = (
        db.prepare('SELECT balance FROM agents WHERE agent_id = ?').get(id) as {
          balance: number;
        }
      ).balance;
      const charged = Math.min(used, row.amount, current);
      db.prepare('DELETE FROM reservations WHERE agent_id = ?').run(id);
      db.prepare(
        'UPDATE agents SET balance = balance - ? WHERE agent_id = ?',
      ).run(charged, id);
      const balance = (
        db.prepare('SELECT balance FROM agents WHERE agent_id = ?').get(id) as {
          balance: number;
        }
      ).balance;
      db.prepare(
        `INSERT INTO transactions(kind, actor, source, amount, source_balance_after)
        VALUES ('consume', ?, ?, ?, ?)`,
      ).run(id, id, charged, balance);
      db.exec('COMMIT');
    } catch (error) {
      try {
        db.exec('ROLLBACK');
      } catch {
        /* transaction did not start */
      }
      throw error;
    } finally {
      db.close();
    }
  });
}
