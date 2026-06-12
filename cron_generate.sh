#!/bin/bash
# Spouštěno 1. den každého měsíce — generuje výkaz za předchozí měsíc.
# Crontab:  0 6 1 * * /home/user/Invoice/cron_generate.sh >> /home/user/Invoice/cron.log 2>&1

set -e
cd "$(dirname "$0")"
echo "[$(date '+%Y-%m-%d %H:%M')] Spouštím generování PDF..."
python3 generate_pdf.py
echo "[$(date '+%Y-%m-%d %H:%M')] Hotovo."
