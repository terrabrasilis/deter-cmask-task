#!/bin/bash
source /etc/environment

# verify if rebuild is enable
if [[ -v FORCE_REBUILD && "${FORCE_REBUILD}" = "yes" ]]; then

    # parse and cast to integer
    START_YEAR=$(echo ${START_YEAR_MONTH} | cut -d'-' -f1)
    START_MONTH=$(echo ${START_YEAR_MONTH} | cut -d'-' -f2)
    START_YEAR=$((${START_YEAR}))
    START_MONTH=$((${START_MONTH}))
    END_YEAR=$(echo ${END_YEAR_MONTH} | cut -d'-' -f1)
    END_MONTH=$(echo ${END_YEAR_MONTH} | cut -d'-' -f2)
    END_YEAR=$((${END_YEAR}))
    END_MONTH=$((${END_MONTH}))

    # iterate over date range to force the rebuild data
    for ((YEAR=$START_YEAR; YEAR<=$END_YEAR; ++YEAR));
    do
        END_MONTH_TMP=$END_MONTH
        if [[ ${END_YEAR} -gt ${YEAR} ]]; then
            END_MONTH_TMP=12
        fi;

        for ((MONTH=$START_MONTH; MONTH<=$END_MONTH_TMP; ++MONTH));
        do
            MONTH_TMP="${MONTH}"
            if [[ ${MONTH} -lt 10 ]]; then
                MONTH_TMP="0${MONTH}"
            fi;
            FORCE_YEAR_MONTH="${YEAR}-${MONTH_TMP}-01"
            echo "FORCE_YEAR_MONTH=${FORCE_YEAR_MONTH}"
            "$SCRIPT_DIR/start.sh"
            echo "======================================"
            echo $(date)
            echo "======================================"
            echo "State of env vars"
            echo "FORCE_REBUILD=${FORCE_REBUILD}"
            echo "FORCE_YEAR_MONTH=${FORCE_YEAR_MONTH}"
            echo "EVERY_DAY=${EVERY_DAY}"
            echo "BASE_URL=${BASE_URL}"
            echo "======================================"
        done
    done

else
    "$SCRIPT_DIR/start.sh"
    echo "======================================"
    echo $(date)
    echo "======================================"
    echo "State of env vars"
    echo "FORCE_REBUILD=${FORCE_REBUILD}"
    echo "FORCE_YEAR_MONTH=${FORCE_YEAR_MONTH}"
    echo "EVERY_DAY=${EVERY_DAY}"
    echo "BASE_URL=${BASE_URL}"
    echo "======================================"
fi;
