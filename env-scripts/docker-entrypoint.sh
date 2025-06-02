#!/bin/bash
## THE ENV VARS ARE NOT READED INSIDE A SHELL SCRIPT THAT RUNS IN CRON TASKS.
## SO, WE WRITE INSIDE THE /etc/environment FILE AND READS BEFORE RUN THE SCRIPT.
echo "export SHARED_DIR=\"$SHARED_DIR\"" >> /etc/environment
echo "export SCRIPT_DIR=\"$SCRIPT_DIR\"" >> /etc/environment
echo "export TZ=\"America/Sao_Paulo\"" >> /etc/environment
echo "export PATH=\"/usr/local/bin:$PATH\"" >> /etc/environment
#
# if defined as env var, its used to force a specific year month to download data.
if [[ -v FORCE_YEAR_MONTH ]]; then
    # The format is: YYYY-MM-DD where DD is always 01
    echo "export FORCE_YEAR_MONTH=\"$FORCE_YEAR_MONTH\"" >> /etc/environment
fi;
# if defined as env var, its used to force the execution every day.
if [[ -v EVERY_DAY ]]; then
    # Expected value is: yes to force or whatever
    echo "export EVERY_DAY=\"$EVERY_DAY\"" >> /etc/environment
fi;
# if defined as env var, its used to force the input BASE_URL from Stack.
if [[ -v BASE_URL ]]; then
    # Expected value is an URL string to load input files
    echo "export BASE_URL=\"$BASE_URL\"" >> /etc/environment
fi;
#
# run cron in foreground
cron -f