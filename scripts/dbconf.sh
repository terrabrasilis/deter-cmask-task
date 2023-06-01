#!/bin/bash
TARGET_FILE=${1}
if [[ -f "${DATA_DIR}/config/pgconfig_${TARGET_FILE}" ]];
then
  source "${DATA_DIR}/config/pgconfig_${TARGET_FILE}"
  export PGUSER=$user
  export PGPASSWORD=$password
  export PGHOST=$host
  export PGPORT=$port
  export PGDB=$database
else
  echo "Missing Postgres config file for target: ${TARGET_FILE}."
  exit
fi