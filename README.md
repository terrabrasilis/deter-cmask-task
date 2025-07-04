## Cloud cover preparation

***Used on the DETER panel.**

Automation or semi-automation to read the cmask data from the HTTP download page, extract the non-cloud pixel values, calculate the cloud coverage rate for counties based on each area of the vector table, and write to the mask table of the database.

The expected periodicity is monthly, at the end of each month, for the acquisition and calculation of new data.

The Geotiff files produced in the process are moved to the download area. The download area must be defined as a container volume in the Stack configuration. See the background-tasks.yaml file in the [docker-stack](https://github.com/terrabrasilis/docker-stacks.git) repository.

## Configurations

Preconditions:

 - SQLViews in DETER databases to deliver standardized data to the download script, such as: satellite, sensor, path_row, view_date and publish_date;
 - Schema and tables for storing the cloud mask data for the last processed month and accumulating the data month by month;
 - Configuration files to provide parameters for connecting to databases, one for each biome: (amazonia and cerrado);
 - Define the environment variables to guide the execution flow;
 - Warning: In the download-data.py script we have some hardcoded definitions. These values may change in the future and must be adjusted directly in the code.
 - Warning: In the insert-final-cloud-cover.sh script, we have the download area as a directory path (/usr/local/download/static/cmask), hardcoded in the code.

### Database configuration SQLView

For each biome we need SQLView to standardize output data, so:

For amazonia:
```sql
-- Gets the data from current table
CREATE OR REPLACE VIEW cloud.deter_current
 AS
 SELECT deter_table.gid || '_curr'::text AS gid,
    ("substring"(deter_table.orbitpoint::text, 0, 4) || '_'::text) || "substring"(deter_table.orbitpoint::text, 4) AS path_row,
    deter_table.date AS view_date,
    deter_table.date_audit,
    deter_table.sensor,
    deter_table.satellite,
    deter_table.publish_month
   FROM deter_table
  WHERE deter_table.date > (( SELECT prodes_reference.end_date FROM prodes_reference))
   AND deter_table.areatotalkm >= 0.01::double precision
   AND deter_table.uf::text <> 'MS'::text
   AND st_geometrytype(deter_table.geom) <> 'ST_LineString'::text;


```

For cerrado:
```sql
-- Gets the data from current table
CREATE OR REPLACE VIEW cloud.deter_current
 AS
 SELECT deter_table.origin_gid || '_curr'::text AS gid,
    deter_table.path_row,
    deter_table.view_date,
    deter_table.created_date AS date_audit,
    deter_table.sensor,
    deter_table.satellite,
    deter_table.publish_month
   FROM deter_cerrado_mun_ucs deter_table
  WHERE deter_table.areatotalkm >= 0.01::double precision;
```

### Database model

For each biome/database we need a schema and two tables to store the cloud mask data, they are:

```sql
-- the cloud schema
CREATE SCHEMA cloud AUTHORIZATION postgres;

-- the ephemeral data table to store the results of the last processing
CREATE TABLE cloud.monthly_cloud_mun_table
(
    id numeric,
    geom geometry(MultiPolygon,4674),
    nm_municip character varying(80),
    cd_geocmu character varying(80),
    uf character varying(80),
    cod_ibge character varying(80),
    area_px_km numeric,
    area_km2 numeric,
    month_cloud_km2 double precision,
    year integer,
    month integer
);

-- the final data table to accumulate month by month data
CREATE TABLE cloud.monthly_cloud_by_municipality
(
    id serial,
    cod_ibge integer NOT NULL,
    month_mm integer NOT NULL,
    year_yyyy integer NOT NULL,
    area_km double precision NOT NULL,
    area_mun_km double precision NOT NULL,
    uf character varying(2) NOT NULL,
    created_at date NOT NULL DEFAULT (now())::date,
    CONSTRAINT monthly_cloud_by_municipality_id_pkey PRIMARY KEY (id)
);
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

 > BASE_URL: Optional parameter to be passed to the container instance. The base URL where the cmask files are located.

 > FORCE_REBUILD: Used to force the reconstruction of all data for a year/month range. Must be used in conjunction with the variables: START_YEAR_MONTH and END_YEAR_MONTH.

 > START_YEAR_MONTH: The starting year/month for the date range in the format: YYYY/MM

 > END_YEAR_MONTH: The ending year/month for the date range in the format: YYYY/MM

The examples for setting these variables inside the docker compose fragment.

To process once for a specific year/month.
```yaml
   ...
   environment:
      # force download and process all cmask for May 2023
      - "FORCE_YEAR_MONTH=2023-05-01"
      - "EVERY_DAY=no"
      - "BASE_URL=http://cbers9.dpi.inpe.br:8089/files"
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

To process once for each year/month for the date range.
```yaml
   ...
   environment:
      - "FORCE_REBUILD=yes"
      - "START_YEAR_MONTH=2024-01"
      - "END_YEAR_MONTH=2025-05"
   ...
```


## Deploy

To deploy this container, we provide an example in docker compose format in the [docker-compose.yaml](./docker-compose.yml) file.

To run it, an example command is:

```sh
# to up the stack
docker compose -f docker-compose.yaml up -d

# and to stop
docker compose -f docker-compose.yaml down
```


## About code

Adapted from the original by Luis Eduardo P. Maurano <luis.maurano@inpe.br>