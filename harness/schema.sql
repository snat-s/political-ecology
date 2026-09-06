CREATE TABLE IF NOT EXISTS pool (
        singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
        balance INTEGER NOT NULL CHECK (balance >= 0)
      );
      CREATE TABLE IF NOT EXISTS agents (
        agent_id TEXT PRIMARY KEY,
        balance INTEGER NOT NULL CHECK (balance >= 0)
      );
      CREATE TABLE IF NOT EXISTS reservations (
        agent_id TEXT PRIMARY KEY REFERENCES agents(agent_id),
        amount INTEGER NOT NULL CHECK (amount > 0)
      );
      CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
        kind TEXT NOT NULL, actor TEXT, source TEXT, destination TEXT,
        amount INTEGER NOT NULL CHECK (amount >= 0),
        source_balance_after INTEGER, destination_balance_after INTEGER
      );
