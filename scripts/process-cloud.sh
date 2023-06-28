#!/bin/bash
TARGET_BIOME=${1}

if [[ -d "${DATA_DIR}/${TARGET_BIOME}" ]];
then
    # go to the work directory
    cd "${DATA_DIR}/${TARGET_BIOME}/"
    echo 
    echo "=========== ${TARGET_BIOME} ================"
    echo 

    # get date reference to load input images
    if [[ -f "acquisition_data_control" ]];
    then
        source "acquisition_data_control"
        year_month=$(date +'%Y%m' -d "${PREVIOUS_MONTH}")
        # if we have an old noncloud file to the same year_month, delete that
        if [[ -f "noncloud_${year_month}_64.tif" ]];
        then
            rm -f ./noncloud_${year_month}_64.*
        fi;
        # print total founded files to log
        echo "Total founded files: `ls ./*${year_month}*.tif |wc -l`"
        echo 
        # control flow
        CRTL=""

        for FILE_NAME in `ls ./*${year_month}*.tif | awk {'print $1'}`
        do
            TIF_NAME=`basename ${FILE_NAME}`
            TIF_NAME=`echo ${TIF_NAME} | cut -d "." -f 1`
            echo ${TIF_NAME}
            gdalwarp -q -t_srs EPSG:4326 -of vrt -tr 0.000575656183491 0.000575656183491 "${FILE_NAME}" /vsistdout/ | gdal_translate -co compress=lzw -a_nodata 0 /vsistdin/ ${TIF_NAME}"_epsg4326.tif"
            gdal_calc.py -A ${TIF_NAME}"_epsg4326.tif" --NoDataValue=0 --co="COMPRESS=LZW" --quiet --outfile=${TIF_NAME}"_epsg4326_nn.tif" --calc="((A==127)*127)"
            CRTL="FORWARD"
        done

        if [[ "${CRTL}" = "FORWARD" ]];
        then

            gdalbuildvrt noncloud_${year_month}_64.vrt *${year_month}*_epsg4326_nn.tif

            if [[ "${TARGET_BIOME}" = "amazonia" ]]; then
                BBOX="-73.9904032605401056 -18.0417666700000012 -43.9518273629147984 5.2718410771729696"
            else
                BBOX="-60.1099291026705842 -24.6851194256049205 -41.5224714772777688 -2.3267091205464463"
            fi

            gdal_translate -of GTiff -co "COMPRESS=LZW" -a_ullr ${BBOX} -co BIGTIFF=YES noncloud_${year_month}_64.vrt noncloud_${year_month}_64.tif
            gdaladdo noncloud_${year_month}_64.tif

            # remove temporary files
            rm -f ./*${year_month}*_epsg4326*.tif
        fi;
    fi;
fi;

# go to the scripts directory
cd ${SCRIPT_DIR}