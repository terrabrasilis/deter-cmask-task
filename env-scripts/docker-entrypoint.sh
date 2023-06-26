#!/bin/bash
## THE ENV VARS ARE NOT READED INSIDE A SHELL SCRIPT THAT RUNS IN CRON TASKS.
## SO, WE WRITE INSIDE THE /etc/environment FILE AND READS BEFORE RUN THE SCRIPT.
echo "export SHARED_DIR=\"$SHARED_DIR\"" >> /etc/environment
echo "export SCRIPT_DIR=\"$SCRIPT_DIR\"" >> /etc/environment
echo "export TZ=\"America/Sao_Paulo\"" >> /etc/environment
#
# used to force a specific year month download data. The format is: YYYY-MM-DD where DD is always 01
echo "export FORCE_YEAR_MONTH=\"$FORCE_YEAR_MONTH\"" >> /etc/environment
#
# run cron in foreground
cron -f