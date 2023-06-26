#!/bin/bash
# to debug in localhost, enable the following two lines
# SCRIPT_DIR=`pwd`
# SHARED_DIR=$SCRIPT_DIR"/../data"

# to store run log
DATE_LOG=$(date +"%Y-%m-%d_%H:%M:%S")
# The data work directory.
DATA_DIR=$SHARED_DIR
export DATA_DIR

# go to the scripts directory
cd ${SCRIPT_DIR}

# list of biomes to export data
BIOMES=("cerrado" "amazonia")

# read postgres params for each database from pgconfig file
for TARGET_BIOME in ${BIOMES[@]}
do
    # the log file for each biome
    LOG_FILE=${TARGET_BIOME}_cmaks_${DATE_LOG}.log
    # load postgres parameters from config file in config/pgconfig
    . ./dbconf.sh "${TARGET_BIOME}" >> ${DATA_DIR}/${LOG_FILE}
    #
    # to read inside python
    export TARGET_BIOME=${TARGET_BIOME}
    # get cmask files scraping download page
    python3 download-data.py >> "${DATA_DIR}/download_${LOG_FILE}"
    #
    # using gdal to extract non cloud pixels (number 127) from cmask files
    . ./process-cloud.sh "${TARGET_BIOME}" >> "${DATA_DIR}/gdal_${LOG_FILE}"
    #
    # build cloud cover by municipalities using cmask files
    python3 zonal-cloud.py >> "${DATA_DIR}/zonal_${LOG_FILE}"
done