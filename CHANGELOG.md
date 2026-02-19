# Changelog

## [0.5.0] — 2026-02-19

### Added
- **Currency conversion**: For English users, all amounts are shown in USD with RUB in parentheses. Real-time exchange rate from CBR API with 5-minute caching.
- **Localized game names and outcomes**: All game names and outcomes now use translation system (EN/RU).
- **Game-specific images**: Each game now shows its own image (`basalt_2dices.png`, `basalt_moreless.png`, etc.) instead of generic game list image.
- **Referrer notifications**: When someone registers using a referral link, the referrer receives a notification with the new user's username.
- **"Change amount" button**: Added to deposit and withdrawal confirmation screens, allowing users to go back and modify the amount without restarting the flow.
- **Admin notifications**: New payment requests (deposit/withdrawal) now send a notification to all admins with user details and inline Approve/Reject buttons.

### Fixed
- **Withdrawal cancel**: Now returns to deposit menu (not account) with updated balance.
- **Balance formatting**: Fixed double ruble sign in Russian language.
- **Deposit screen**: Fixed `{mode}` and `{balance}` placeholders not being replaced with actual values.
- **Game descriptions**: Improved formatting with bullet points and proper line breaks.
- **Insufficient balance message**: Withdrawal now shows correct message without demo mode references.

### Changed
- **GAME_LIST structure**: Replaced hardcoded names with `name_key` and `outcome_keys` for proper localization.
- **Middleware order**: CurrencyMiddleware now runs right after BotInjectMiddleware to ensure USD rate is available in all handlers.
- **Image naming**: Standardized image naming convention for all game screens.

### Removed
- **MySQL sync**: Removed all MySQL-related code (schemas, migrations, sync services) as we now use SQLite exclusively.
- **WebApp CGI**: Removed CGI scripts in favor of Flet web application.

---

## [0.4.0] — 2026-02-18

### Added
- **Flet web application**: Replaced CGI-based statistics with a modern Flet web app.
- **Advanced statistics filters**: Users can now filter games by type, date range, and number of games.
- **Game cards**: Redesigned game history display with cards showing game image, outcome, coefficient, bet amount, and result.
- **Responsive design**: Web app now works perfectly on mobile devices within Telegram WebView.

### Changed
- **Statistics menu**: Simplified to just "View statistics" button (opens Flet web app) and "Back".
- **Data flow**: Web app now reads directly from SQLite (same database as bot), eliminating sync delays.

### Fixed
- **WebApp deployment**: Resolved CGI configuration issues by switching to Flet's built-in web server.

---

## [0.3.0] — 2026-02-17

### Added
- **Withdraw functionality**: Users can now request withdrawals (real mode only) with preset amounts or custom input.
- **Contact verification**: One-time contact sharing required for payment requests.
- **Payment status tracking**: Users can view their pending/approved/rejected requests.
- **Admin payment processing**: Admins receive notifications for new requests and can approve/reject them directly from chat.

### Fixed
- **Demo restore**: Fixed 24h cooldown logic and proper balance reset.
- **Fast mode**: Game results now show immediately when fast mode is enabled.
- **Double-tap protection**: Prevented users from placing multiple bets on the same confirmation message.

---

## [0.2.0] — 2026-02-15

### Added
- **Eight games**: Full implementation of all 8 games with proper win/loss resolution.
- **Bet amount presets**: Users can choose from predefined amounts or enter custom values.
- **Confirmation screen**: Shows game details, outcome, bet amount, coefficient, probability, potential win, current and potential balance.
- **Game result screens**: Win/loss messages with images and action buttons (Repeat, Choose game, Main menu).
- **Demo mode**: 50,000 ₽ virtual balance with 24h restore cooldown.

### Changed
- **Game flow**: Complete rewrite of game handlers with proper state management and double-tap protection.
- **Balance updates**: Real-time balance updates after bets and wins.

---

## [0.1.0] — 2026-02-14

### Added
- **Project structure**: Clean architecture with handlers, services, database layers.
- **Telegram bot**: aiogram 3.x implementation with /start, /info, /help, /admin commands.
- **User system**: Registration, language preferences (EN/RU), notification settings, fast mode toggle.
- **Account menu**: Profile, statistics, settings, mode switching (demo/real), deposit, language.
- **Basic games**: Initial implementation of game selection and outcome choice.
- **Admin panel**: User management, casino settings, broadcast functionality.
- **Database**: SQLite with 3NF schema, migrations, Pydantic models.
- **Referral system**: Signed referral links with bonus processing.
- **Backup system**: Automatic daily backups with 30-day retention for games and 14-day for payment requests.
- **Docker**: Dockerfile and docker-compose for easy deployment.
- **CI/CD**: GitHub Actions with linting and testing.

### Technical
- Middleware: TechWork, UserBlock, DemoRestore, Logging, BotInject.
- Services: game logic, balance management, referral processing, stats calculation.
- Queries: Separate modules for users, games, payments, referrals, settings.
- Localization: EN/RU text templates with get_text() function.