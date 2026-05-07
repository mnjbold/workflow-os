# Workflow OS Makefile

.PHONY: help install setup test run clean

help:
	@echo "Workflow OS - Available commands:"
	@echo "  make install    - Install Python dependencies"
	@echo "  make setup      - Setup configuration files"
	@echo "  make test       - Test the monitor"
	@echo "  make run-api    - Run FastAPI server"
	@echo "  make run-monitor - Run monitor once"
	@echo "  make cron-setup - Setup OpenClaw cron job"
	@echo "  make cron-logs  - View cron job logs"
	@echo "  make clean      - Clean temporary files"

install:
	pip install -r requirements.txt

setup:
	mkdir -p config data logs
	@if [ ! -f config/config.yaml ]; then \
		cp config/config.example.yaml config/config.yaml; \
		echo "Created config/config.yaml - please edit with your settings"; \
	fi

test:
	python eod_monitor.py --test

run-api:
	cd api && uvicorn main:app --reload --port 8000

run-monitor:
	python eod_monitor.py

cron-setup:
	./setup_cron.sh

cron-logs:
	openclaw cron logs eod-monitor --tail 100

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -f data/*.db logs/*.log
