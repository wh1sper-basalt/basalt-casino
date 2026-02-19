# BASALT Casino — Telegram bot
FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY bot/ bot/
COPY Makefile ./

# Default: run bot (migrations run on startup via init_db)
CMD ["python", "-m", "bot.main"]
