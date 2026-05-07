#!/bin/bash
# Setup OpenClaw cron job for EOD monitor

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "Setting up EOD monitor cron job..."

# Create the cron job using OpenClaw
openclaw cron create \
  --name eod-monitor \
  --schedule "*/15 * * * *" \
  --command "python ${SCRIPT_DIR}/eod_monitor.py" \
  --description "Monitor Google Drive for new EOD reports"

echo "Cron job created!"
echo ""
echo "To view status:"
echo "  openclaw cron list"
echo ""
echo "To view logs:"
echo "  openclaw cron logs eod-monitor"
echo ""
echo "To delete:"
echo "  openclaw cron delete eod-monitor"
