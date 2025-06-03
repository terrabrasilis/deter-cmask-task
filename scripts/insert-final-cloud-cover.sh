#!/bin/bash
#
# define the psql location tool and database conection string
PG_BIN="/usr/bin"
PG_CON="-d ${PGDB} -U ${PGUSER} -h ${PGHOST} -p ${PGPORT}"

year=$(date +'%Y' -d "${PREVIOUS_MONTH}")
month=$(date +'%m' -d "${PREVIOUS_MONTH}")
CHECK_DATA="WITH test AS ("
CHECK_DATA="${CHECK_DATA} SELECT COUNT(*) as tt"
CHECK_DATA="${CHECK_DATA} FROM cloud.monthly_cloud_mun_table"
CHECK_DATA="${CHECK_DATA} WHERE year=${year} AND month=${month}"
CHECK_DATA="${CHECK_DATA} AND month_cloud_km2 > 0.0"
CHECK_DATA="${CHECK_DATA} ) SELECT CASE WHEN tt > 0 THEN 'YES' ELSE 'NO' END FROM test"

CHECK_DATA=($(${PG_BIN}/psql ${PG_CON} -t -c "${CHECK_DATA};"))

if [[ "YES" = "${CHECK_DATA}" ]]; then
    # used to delete old values if exists on table
    DELETE="WITH candidates AS ( "
    DELETE="${DELETE} SELECT month as mm, year as yy "
    DELETE="${DELETE} FROM cloud.monthly_cloud_mun_table "
    DELETE="${DELETE} GROUP BY 1,2 "
    DELETE="${DELETE} ) "
    DELETE="${DELETE} DELETE FROM cloud.monthly_cloud_by_municipality WHERE year_yyyy=(SELECT yy FROM candidates) AND month_mm=(SELECT mm FROM candidates);"

    # used to insert new results on final cloud table
    INSERT="INSERT INTO cloud.monthly_cloud_by_municipality(cod_ibge, month_mm, year_yyyy, area_km, area_mun_km, uf) "
    INSERT="${INSERT} SELECT cod_ibge::integer, month as month_mm, year as year_yyyy, month_cloud_km2 as area_km, area_px_km, uf "
    INSERT="${INSERT} FROM cloud.monthly_cloud_mun_table "
    INSERT="${INSERT} WHERE month_cloud_km2 > 0.0;"


    ${PG_BIN}/psql ${PG_CON} -t -c "${DELETE}"

    ${PG_BIN}/psql ${PG_CON} -t -c "${INSERT}"

    # store the final geotiff to send to the download area
    # The download area is defined as the container volume in the Stack configuration. (/usr/local/download/static/cmask)
    mkdir ${DATA_DIR}/${TARGET_BIOME}/final_files
    mv ${DATA_DIR}/${TARGET_BIOME}/noncloud_${year}${month}_64.tif /usr/local/download/static/cmask/${TARGET_BIOME}/noncloud_${year}${month}_64.tif
    # remove downloaded and temporary files
    rm -f ${DATA_DIR}/${TARGET_BIOME}/*${year_month}*.{tif,vrt}
fi;