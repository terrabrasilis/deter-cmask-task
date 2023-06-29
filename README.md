## Cloud cover preparation

***Used on the DETER panel.**

Automation or semi-automation to read the cmask data from the HTTP download page, extract the non-cloud pixel values, calculate the cloud coverage rate for counties based on each area of the vector table, and write to the mask table of the database.

The expected periodicity is monthly, at the end of each month, for the acquisition and calculation of new data.

## Configurations

Preconditions:

 - SQLViews in DETER databases to deliver standardized data to the download script, such as: satellite, sensor, path_row, view_date and publish_date;
 - Configuration files to provide parameters for connecting to databases, one for each biome: (amazonia and cerrado);
 - Define the environment variables to guide the execution flow;

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

### Environment variables

To control the execution, we can define the environment variables as follows.

The default value for these variables is 'no' if not defined.

 > FORCE_YEAR_MONTH: if defined, its used to force a specific year month to download data. The expected format is: YYYY-MM-DD where DD is always 01. Do not set the EVERY_DAY or set to "EVERY_DAY=no".

 > EVERY_DAY: if defined and the value is not  equal 'no' ("EVERY_DAY=no"), its used to skip checking "if the last month is closed" and the flow is forced to happen every day. If the value equals 'yes' ("EVERY_DAY=yes"), don't use FORCE_YEAR_MONTH together because it will download the same data every day, or set to default "FORCE_YEAR_MONTH=no".

The examples for setting these variables inside the docker compose fragment.

To process once for a specific year/month.
```yaml
   ...
   environment:
      # force download and process all cmask for May 2023
      - "FORCE_YEAR_MONTH=2023-05-01"
      - "EVERY_DAY=no"
   ...
```

To process every day:
```yaml
   # like this
   ...
   environment:
      - "FORCE_YEAR_MONTH=no"
      # force download and process of cmask on all days of the current month
      - "EVERY_DAY=yes"
   ...

   # does the same thing as
   ...
   environment:
      # force download and process of cmask on all days of the current month
      - "EVERY_DAY=yes"
   ...
```

To process once for each closed month.
```yaml
   ...
   environment:
      # set the default value for the variables or remove the "environment" block from the compose
      - "FORCE_YEAR_MONTH=no"
      - "EVERY_DAY=no"
   ...
```