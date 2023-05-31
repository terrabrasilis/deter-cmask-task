## Cloud cover preparation

***Used on the DETER panel.**

Automation or semi-automation to read the cmask data from the HTTP download page, extract the non-cloud pixel values, calculate the cloud coverage rate for counties based on each area of the vector table, and write to the mask table of the database.

The expected periodicity is monthly, at the end of each month, for the acquisition and calculation of new data.

## Configurations

It needs a configuration file to compose the execution environment, as follows:

 - config/pgconfig_<biome_name> (database settings to read and write data)

Create a data directory to write the output files and the "config" directory inside. In this directory, we place the pgconfig.

### Config details

 > Content of pgconfig file
```txt
user="postgres"
host="localhost"
port="5432"
database="db_name"
password="postgres"
```
