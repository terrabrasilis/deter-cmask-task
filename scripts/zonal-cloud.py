# -*- coding: utf-8 -*-
"""
Compute the number of non cloud pixels by municipalities

Copyright 2023 TerraBrasilis

Notes about code.

Created on Mon Jan 30 14:02:30 2023

@author: Luis Maurano

@mainteiner: Andre Carvalho
"""

import psycopg2
import rasterio
import geopandas as gpd
import pandas as pd
from shapely.geometry import mapping
from rasterio.mask import mask
import numpy as np
from datetime import datetime
import math
import os
import urllib
from sqlalchemy import create_engine

class ZonalCloud:
    """
    Build the non cloud mosaic image based on CMASK images.
    """

    def __init__(self, dir=None):
        """
        Constructor with predefined settings.

        Optional parameters:
        -----------------------------
        :param:dir: The base directory for writing downloaded data.

        To define configurations on instantiate, use the environment variables with sensitive data and other settings.

        Mandatory parameters (via env vars):
        ------------------------------
        :env:TARGET_BIOME: The name of the biome. Accepted values are: amazonia or cerrado
        :env:PGHOST: The host name or IP to connect to database
        :env:PGUSER: The user name to connect to database
        :env:PGPASSWORD: The password to connect to database
        :env:PGDB: The database name to connect to

        Optional parameters (via env vars):
        -----------------------------
        :env:PGPORT: The port number to connect to database (default is 5432)
        """
        # Data directory for writing downloaded data
        self.DIR=dir if dir else os.path.realpath(os.path.join(os.path.dirname(__file__),"../data/"))
        self.DIR=os.getenv("DATA_DIR", self.DIR)
        # database params
        self.host=os.getenv("PGHOST", 'host')
        self.database=os.getenv("PGDB", 'database')
        self.port=os.getenv("PGPORT", '5432')
        self.user=os.getenv("PGUSER", 'user')
        self.password=os.getenv("PGPASSWORD", 'password')
        #
        # the current biome name
        self.BIOME=os.getenv("TARGET_BIOME", 'amazonia')
        #
        # start configs for each biome
        self.__configForBiome()

    def __configForBiome(self):
        # define the base directory to store downloaded data
        self.DATA_DIR="{0}/{1}".format(self.DIR,self.BIOME)
        # try read year and month from control file related of the last downloaded files
        self.YEAR, self.MONTH=self.__getPreviousMonthFromMetadata()
        # the table name when we get the vectors (zones) and store the results
        self.zonal_table = "cloud.monthly_cloud_mun_table"
        # define connection with db based in biome
        self.con = psycopg2.connect(host=self.host, port=self.port, database=self.database, user=self.user, password=self.password)
        self.con.cursor().execute("SET application_name = 'ETL - DETER CMask Task';")
        password_updated = urllib.parse.quote_plus(self.password)
        url = f"postgresql+psycopg2://{self.user}:{password_updated}@{self.host}:{self.port}/{self.database}"
        self.engine = create_engine(url=url)

    def __getPreviousMonthFromMetadata(self):
        """
        Read previous month from download control file
        """
        year=month=None
        output_file="{0}/acquisition_data_control".format(self.DATA_DIR)
        if os.path.exists(output_file):
            with open(output_file) as f:
                lines=f.readlines()
                for line in lines:
                    if line.split("=")[0]=="PREVIOUS_MONTH":
                        pm=line.split("=")[1]
                        pm=pm.strip()
                        pm=pm.strip('"')
                        year=datetime.strptime(str(pm),'%Y-%m-%d').strftime('%Y')
                        month=datetime.strptime(str(pm),'%Y-%m-%d').strftime('%m')
        return year,month

    def __getZonalAreas(self):
        """
        Build the geo data frame with municipality vectors and related parameters
        """

        SQL=f"SELECT cod_ibge, area_px_km, geom"
        SQL=f"{SQL} FROM {self.zonal_table}"
        SQL=f"{SQL} ORDER BY cod_ibge ASC"

        zonals=None
        try:
            zonals = gpd.GeoDataFrame.from_postgis(SQL, self.engine)
        except Exception as error:
            raise error

        return zonals
    
    def __getNonCloudInfos(self):
        """
        Open the non cloud geotif file and compute the pixel area.
        Return tuple:
        -----------
          noncloud_data: the reference to the non cloud file on memory
          pixel_area: the pixel area numeric value.
        """
        noncloud_data=pixel_area=None

        filename="{0}/noncloud_{1}{2}_64.tif".format(self.DATA_DIR, self.YEAR, self.MONTH)
        if os.path.exists(filename):
            noncloud_data = rasterio.open(filename)
            pixelSizeX, pixelSizeY  = noncloud_data.res
            resX = (pixelSizeX * math.pi/180) * 6378000
            resY = (pixelSizeY * math.pi/180) * 6378000
            pixel_area = abs((resX * resY)/1000000)

        return noncloud_data,pixel_area

    def execute(self):

        zonals=self.__getZonalAreas()
        noncloud_data,pixel_area=self.__getNonCloudInfos()
        if not zonals is None and not noncloud_data is None and not pixel_area is None:
            try:
                for _, row in zonals.iterrows():
                    geoms = [mapping(row.geom)]
                    cod_ibge = row.cod_ibge
                    area_mun = row.area_px_km
                    out_image, out_transform = mask(noncloud_data, geoms, nodata=0, crop=True)
                    unique, counts = np.unique(out_image[0], return_counts=True)
                    unique_counts = np.asarray((unique, counts)).T
                    counts = pd.DataFrame(unique_counts)
                    
                    for _, count in counts.iterrows():
                        pixel_value=count[0] # the specific pixel value that exists inside a polygon
                        count_pixels=count[1] # how many pixels are inside a polygon for the specific pixel value
                        if pixel_value > 0:
                            area_nnuvem = pixel_area * count_pixels
                            cloud_area_by_mun = area_mun - area_nnuvem
                        else:
                            cloud_area_by_mun = area_mun
                    query  = f"UPDATE {self.zonal_table} SET month_cloud_km2 = {str(cloud_area_by_mun)}, year={int(self.YEAR)}, month={int(self.MONTH)} WHERE cod_ibge = '{str(cod_ibge)}';"
                    self.con.cursor().execute(query)
                # after all updates, confirm the changes
                self.con.commit()
            except Exception as error:
                print("Failure on write new cloud areas into database.")
                print(f"Exception error message: {str(error)}")
                self.con.rollback()
                raise error
            finally:
                if self.con.closed==0:
                    self.con.close()

# end of class

# Call zonal for build data
znc=ZonalCloud()
znc.execute()