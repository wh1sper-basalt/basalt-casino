# BASALT Casino — Architecture

## Layers

1. **Handlers** (aiogram routers) — receive updates, call services, send messages. No business logic.
2. **Services** — game resolution, balance operations, referral logic, stats, demo restore. No Telegram imports.
3. **Database** — aiosqlite, one global connection; queries in `database/queries/`, Pydantic models in `database/models/`.

## Middleware order

1. **BotInjectMiddleware** — puts `bot` into `data` for handlers.
2. **TechWorkMiddleware** — blocks by `tech_works_global`, `tech_works_demo`, `tech_works_real` from `settings`.
3. **UserBlockMiddleware** — blocks by `is_blocked` / `block_type` (full: only stats; partial: no real mode / withdraw).
4. **DemoRestoreMiddleware** — sets `need_demo_restore` when demo mode and balance &lt; min_bet.
5. **LoggingMiddleware** — logs incoming updates.

## Config

- **Runtime config** (from .env): `bot/config.py` — Pydantic Settings. Admin IDs, DB path, optional Telegraph/WebApp URLs.
- **Casino config** (in DB): table `settings` (single row) — min_bet, max_bet, coefficients, referral_bonus, demo_balance, tech_works flags. Editable via admin panel.

## Data flow examples

- **Start:** Handler parses deep_link → referral service validates link → user/referral created → balance/demo_accounts/user_stats initialized from settings.
- **Game:** Handler gets outcome + amount → balance service checks/deducts → send dice → game service resolves outcome → balance credit + save game + update user_stats.
- **Deposit/withdraw:** Handler creates payment_request (pending) → admin approves → balance service credit_deposit / deduct_withdraw + user_stats update.

## Backup

Background task every 24h: on 1st of month creates gzipped dump in `backups/` (keeps last 3). Daily cleanup: games older than 30 days, completed payment_requests older than 14 days.
