#!/bin/bash
# to debug in localhost, enable the following two lines
SCRIPT_DIR=`pwd`
SHARED_DIR=$SCRIPT_DIR"/../data"

# to store run log
DATE_LOG=$(date +"%Y-%m-%d_%H:%M:%S")
# The data work directory.
DATA_DIR=$SHARED_DIR
export DATA_DIR

# go to the scripts directory
cd $SCRIPT_DIR

# list of biomes to export data
BIOMES=("cerrado" "amazonia")

# read postgres params for each database from pgconfig file
for TARGET_BIOME in ${BIOMES[@]}
do
    # load postgres parameters from config file in config/pgconfig
    . ./dbconf.sh "${TARGET_BIOME}"
    #
    # to read inside python
    export TARGET_BIOME=${TARGET_BIOME}
    # get focuses for previous day
    python3 download-data.py
done