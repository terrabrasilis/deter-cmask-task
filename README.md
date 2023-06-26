## Cloud cover preparation

***Used on the DETER panel.**

Automation or semi-automation to read the cmask data from the HTTP download page, extract the non-cloud pixel values, calculate the cloud coverage rate for counties based on each area of the vector table, and write to the mask table of the database.

The expected periodicity is monthly, at the end of each month, for the acquisition and calculation of new data.

## Configurations

Preconditions:

 - SQLViews in DETER databases to deliver standardized data to the download script, such as: satellite, sensor, path_row, view_date and publish_date;
 - Configuration files to provide parameters for connecting to databases, one for each biome: (amazonia and cerrado);

### Database configuration SQLView

For each biome we need SQLView to standardize output data, so:

For amazonia:
```sql
-- Gets the data from current table
CREATE OR REPLACE VIEW cloud.deter_current
 AS
 SELECT deter_table.gid || '_curr'::text AS gid,
    substring(deter_table.orbitpoint,0,4) ||'_'|| substring(deter_table.orbitpoint,4) AS path_row,
    deter_table.date AS view_date,
    deter_table.sensor,
    deter_table.satellite,
    deter_table.publish_month
   FROM terrabrasilis.deter_table as deter_table
  WHERE deter_table.date > (( SELECT prodes_reference.end_date
           FROM prodes_reference)) AND deter_table.areatotalkm >= 0.01::double precision AND deter_table.uf::text <> 'MS'::text AND st_geometrytype(deter_table.geom) <> 'ST_LineString'::text;

```

For cerrado:
```sql
-- Gets the data from current table
CREATE OR REPLACE VIEW cloud.deter_current
 AS
 SELECT deter_table.origin_gid || '_curr'::text AS gid,
    deter_table.path_row,
    deter_table.view_date,
    deter_table.sensor,
    deter_table.satellite,
    deter_table.publish_month
   FROM public.deter_cerrado_mun_ucs as deter_table
  WHERE deter_table.areatotalkm >= 0.01::double precision;
```

### Database configuration file

It needs a configuration file to compose the execution environment, as follows:

 - config/pgconfig_<biome_name> (database settings to read and write data)

Create a data directory to write the output files and the "config" directory inside. In this directory, we place the pgconfig.

#### Config details

 > Content of pgconfig file
```txt
user="postgres"
host="localhost"
port="5432"
database="db_name"
password="postgres"
```
