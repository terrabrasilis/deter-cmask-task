#!/bin/bash
#
# define the psql location tool and database conection string
PG_BIN="/usr/bin"
PG_CON="-d ${PGDB} -U ${PGUSER} -h ${PGHOST} -p ${PGPORT}"

# used to delete old values if exists on table
DELETE="WITH candidates AS ( "
DELETE="${DELETE} SELECT month as mm, year as yy "
DELETE="${DELETE} FROM cloud.monthly_cloud_mun_table "
DELETE="${DELETE} GROUP BY 1,2 "
DELETE="${DELETE} ) "
DELETE="${DELETE} FROM cloud.monthly_cloud_by_municipality WHERE year_yyyy=(SELECT yy FROM candidates) AND month_mm=(SELECT mm FROM candidates);"

# used to insert new results on final cloud table
INSERT="INSERT INTO cloud.monthly_cloud_by_municipality(cod_ibge, month_mm, year_yyyy, area_km, area_mun_km, uf) "
INSERT="${INSERT} SELECT cod_ibge::integer, month as month_mm, year as year_yyyy, month_cloud_km2 as area_km, area_px_km, uf "
INSERT="${INSERT} FROM cloud.monthly_cloud_mun_table "
INSERT="${INSERT} WHERE month_cloud_km2 > 0.0;"


${PG_BIN}/psql ${PG_CON} -t -c "${DELETE}"

${PG_BIN}/psql ${PG_CON} -t -c "${INSERT}"