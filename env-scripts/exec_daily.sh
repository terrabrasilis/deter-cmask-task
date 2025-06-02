#!/bin/bash
source /etc/environment
"$SCRIPT_DIR/start.sh"
echo "======================================"
echo $(date)
echo "======================================"
echo "State of env vars"
echo "FORCE_YEAR_MONTH=${FORCE_YEAR_MONTH}"
echo "EVERY_DAY=${EVERY_DAY}"
echo "BASE_URL=${BASE_URL}"
echo "======================================"