.PHONY: run migrate backup clean test install

run:
	python -m bot.main

migrate:
	python -m bot.database.connection

backup:
	python -m bot.utils.backup

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

test:
	pytest tests/ -v

install:
	pip install -r requirements.txt
