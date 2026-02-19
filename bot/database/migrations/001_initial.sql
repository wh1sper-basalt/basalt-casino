-- BASALT Casino — начальная схема БД (3НФ)
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT NOT NULL DEFAULT '',
    last_name TEXT,
    full_name TEXT NOT NULL DEFAULT '',
    referral_link TEXT UNIQUE,
    created_at TEXT NOT NULL,
    is_blocked INTEGER NOT NULL DEFAULT 0,
    block_type TEXT,
    language TEXT NOT NULL DEFAULT 'en',
    notifications_enabled INTEGER NOT NULL DEFAULT 1,
    fast_mode INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS user_balances (
    user_id INTEGER PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
    real_balance INTEGER NOT NULL DEFAULT 0,
    demo_balance INTEGER NOT NULL DEFAULT 0,
    demo_mode INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS referrals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users(user_id),
    referrer_id INTEGER NOT NULL REFERENCES users(user_id),
    created_at TEXT NOT NULL,
    bonus_credited INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS demo_accounts (
    user_id INTEGER PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
    last_reset TEXT,
    reset_count INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS games (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(user_id),
    game_type TEXT NOT NULL,
    game_id INTEGER NOT NULL,
    bet_amount INTEGER NOT NULL,
    outcome TEXT NOT NULL,
    is_win INTEGER NOT NULL,
    win_amount INTEGER NOT NULL,
    is_demo INTEGER NOT NULL,
    played_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS payment_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(user_id),
    request_type TEXT NOT NULL,
    amount INTEGER NOT NULL,
    status TEXT NOT NULL,
    payment_method TEXT,
    payment_details TEXT,
    created_at TEXT NOT NULL,
    processed_at TEXT,
    processed_by INTEGER
);

CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    min_bet INTEGER NOT NULL,
    max_bet INTEGER NOT NULL,
    win_coefficient REAL NOT NULL,
    referral_bonus INTEGER NOT NULL,
    demo_balance INTEGER NOT NULL,
    deposit_commission REAL DEFAULT 0,
    tech_works_global INTEGER NOT NULL DEFAULT 0,
    tech_works_demo INTEGER NOT NULL DEFAULT 0,
    tech_works_real INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS user_stats (
    user_id INTEGER PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
    total_games INTEGER NOT NULL DEFAULT 0,
    total_wins INTEGER NOT NULL DEFAULT 0,
    total_losses INTEGER NOT NULL DEFAULT 0,
    total_deposited INTEGER NOT NULL DEFAULT 0,
    total_withdrawn INTEGER NOT NULL DEFAULT 0,
    total_won INTEGER NOT NULL DEFAULT 0,
    total_lost INTEGER NOT NULL DEFAULT 0,
    last_updated TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_games_user_played ON games(user_id, played_at);
CREATE INDEX IF NOT EXISTS idx_games_played_at ON games(played_at);
CREATE INDEX IF NOT EXISTS idx_payment_requests_user ON payment_requests(user_id);
CREATE INDEX IF NOT EXISTS idx_payment_requests_status_created ON payment_requests(status, created_at);
CREATE INDEX IF NOT EXISTS idx_referrals_referrer ON referrals(referrer_id);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username) WHERE username IS NOT NULL;

CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL
);
INSERT OR IGNORE INTO schema_version (version, applied_at) VALUES (1, datetime('now'));
