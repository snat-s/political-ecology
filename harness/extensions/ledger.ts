/** SQLite accounts and the two public token tools. */
import {DatabaseSync} from 'node:sqlite';
import type {ExtensionAPI} from '@earendil-works/pi-coding-agent';
import {Type} from 'typebox';

const COMMON_POOL = 'common-pool';

export function requiredEnvironment(name: string): string {
  const value = process.env[name];
  if (!value) throw new Error(`Missing required environment variable ${name}`);
  return value;
}

function positiveInteger(value: number): number {
  if (!Number.isSafeInteger(value) || value <= 0) {
    throw new Error('amount must be a positive integer');
  }
  return value;
}

export function openLedger(): DatabaseSync {
  // The fleet creates all accounts before starting Pi; tools never invent IDs.
  const db = new DatabaseSync(requiredEnvironment('POLITICAL_ECOLOGY_LEDGER'));
  db.exec('PRAGMA busy_timeout=30000');
  return db;
}

export function agentId(): string {
  const id = requiredEnvironment('POLITICAL_ECOLOGY_AGENT_ID');
  if (id === COMMON_POOL) throw new Error('Invalid agent identity');
  return id;
}

export function registerTokenTools(pi: ExtensionAPI) {
  pi.registerTool({
    name: 'count_tokens',
    label: 'Count Tokens',
    description: 'Counts your remaining tokens.',
    parameters: Type.Object({}, {additionalProperties: false}),
    async execute() {
      const id = agentId();
      const db = openLedger();
      try {
        const row = db
          .prepare('SELECT balance FROM agents WHERE agent_id = ?')
          .get(id) as {balance: number} | undefined;
        if (!row) throw new Error(`Unknown agent account: ${id}`);
        return {
          content: [{type: 'text', text: String(row.balance)}],
          details: {balance: row.balance},
        };
      } catch (error) {
        return {
          content: [{type: 'text', text: (error as Error).message}],
          details: {},
          isError: true,
        };
      } finally {
        db.close();
      }
    },
  });

  pi.registerTool({
    name: 'get_tokens',
    label: 'Get Tokens',
    description:
      'Gets tokens.\nget_tokens(100)\nget_tokens(100, "common-pool")',
    parameters: Type.Object(
      {
        amount: Type.Integer({minimum: 1}),
        source: Type.Optional(Type.String({minLength: 1})),
      },
      {additionalProperties: false},
    ),
    async execute(_toolCallId, params) {
      const destination = agentId();
      const source = params.source ?? COMMON_POOL;
      let amount: number;
      try {
        amount = positiveInteger(params.amount);
        if (source === destination)
          throw new Error('source and destination must differ');
      } catch (error) {
        return {
          content: [{type: 'text', text: (error as Error).message}],
          details: {},
          isError: true,
        };
      }

      const db = openLedger();
      try {
        db.exec('BEGIN IMMEDIATE');
        const destinationRow = db
          .prepare('SELECT balance FROM agents WHERE agent_id = ?')
          .get(destination) as {balance: number} | undefined;
        if (!destinationRow)
          throw new Error(`Unknown agent account: ${destination}`);

        const sourceRow =
          source === COMMON_POOL
            ? (db
                .prepare('SELECT balance FROM pool WHERE singleton = 1')
                .get() as {balance: number} | undefined)
            : (db
                .prepare('SELECT balance FROM agents WHERE agent_id = ?')
                .get(source) as {balance: number} | undefined);
        if (!sourceRow) throw new Error(`Unknown source account: ${source}`);
        const available = sourceRow.balance;
        if (available < amount) {
          throw new Error(
            `${source} has ${available} available tokens; ${amount} requested`,
          );
        }

        if (source === COMMON_POOL) {
          db.prepare(
            'UPDATE pool SET balance = balance - ? WHERE singleton = 1',
          ).run(amount);
        } else {
          db.prepare(
            'UPDATE agents SET balance = balance - ? WHERE agent_id = ?',
          ).run(amount, source);
        }
        db.prepare(
          'UPDATE agents SET balance = balance + ? WHERE agent_id = ?',
        ).run(amount, destination);
        const balance = destinationRow.balance + amount;
        const sourceBalance = sourceRow.balance - amount;
        const transactionKind = 'transfer';
        db.prepare(
          `INSERT INTO transactions
          (kind, actor, source, destination, amount, source_balance_after, destination_balance_after)
          VALUES (?, ?, ?, ?, ?, ?, ?)`,
        ).run(
          transactionKind,
          destination,
          source,
          destination,
          amount,
          sourceBalance,
          balance,
        );
        db.exec('COMMIT');
        return {
          content: [{type: 'text', text: String(balance)}],
          details: {balance},
        };
      } catch (error) {
        try {
          db.exec('ROLLBACK');
        } catch {
          /* transaction did not start */
        }
        return {
          content: [{type: 'text', text: (error as Error).message}],
          details: {},
          isError: true,
        };
      } finally {
        db.close();
      }
    },
  });
}
