#!/bin/bash
source /etc/environment
"$SCRIPT_DIR/start.sh"
echo "======================================"
echo $(date)
echo "======================================"
echo "Using force year month from env var"
echo "FORCE_YEAR_MONTH=${FORCE_YEAR_MONTH}"
echo "======================================"