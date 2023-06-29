# -*- coding: utf-8 -*-
"""
Download via HTTP
Download CMASK geotifs for DETER monthly mosaics

Copyright 2023 TerraBrasilis

Notes about code.

Created on Thu Oct 22 14:06:43 2020

@author: Luis Maurano

@mainteiner: Andre Carvalho
"""

import requests
import psycopg2
from bs4 import BeautifulSoup
import re
import os
from datetime import datetime

class DownloadCMASK:
  """
  Using scraping techniques to locate and download the CMASK files related to the satellite scenes used to
  detect disturbances in the natural vegetation cover of the Amazon and Cerrado biomes, from the DETER project.

  The period is the last month based on the current calendar month when the script is run.
  """

  def __init__(self, dir=None, url=None):
    """
    Constructor with predefined settings.

    Optional parameters:
    -----------------------------
    :param:dir: The base directory for writing downloaded data.
    :param:url: The base URL of download page service.

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
    # the base URL of download page service
    self.BASE_URL=url if url else 'http://www.dpi.inpe.br/catalog/tmp'
    self.BASE_URL=os.getenv("BASE_URL", self.BASE_URL)
    # the satellite list to generate the subpath list
    self.SATELLITES=['CBERS_4','CBERS_4A','AMAZONIA_1']
    #
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
    # used to force one specific year_month to download
    self.FORCE_YEAR_MONTH=os.getenv("FORCE_YEAR_MONTH", 'no')
    # validation entry
    try:
      datetime.strptime(str(FORCE_YEAR_MONTH),'%Y-%m-%d')
    except Exception as ex:
      FORCE_YEAR_MONTH='no'
      print("Variable FORCE_YEAR_MONTH is wrong and force to default 'no'")
      print(f"Error: {str(ex)}")
    #
    # used to skip checking "if the last month is closed" and the flow is forced to happen every day.
    self.EVERY_DAY=os.getenv("EVERY_DAY", 'no') if self.FORCE_YEAR_MONTH=='no' else 'no'

    # year and month to compose the URL used to download cmask
    self.YEAR_MONTH,self.PUBLISH_MONTH=self.__getCurrentYearMonth()

  def __configForBiome(self):
    # define the base directory to store downloaded data
    self.DATA_DIR="{0}/{1}".format(self.DIR,self.BIOME)
    # create the output directory if it not exists
    os.makedirs(self.DATA_DIR, exist_ok=True)
    # try read previous month from control file
    self.PREVIOUS_MONTH=self.__getPreviousMonthFromMetadata()

    # define connection with db based in biome
    self.con = psycopg2.connect(host=self.host, port=self.port, database=self.database, user=self.user, password=self.password)

  def __buildQuery(self, satellite):

    satellite = satellite.replace('_', '-')
    max_year_month = f"(SELECT MAX(publish_month) FROM cloud.deter_current)" if self.FORCE_YEAR_MONTH=='no' else f"'{self.FORCE_YEAR_MONTH}'::date"

    SQL=f"SELECT satellite, path_row, view_date"
    SQL=f"{SQL} FROM cloud.deter_current"
    SQL=f"{SQL} WHERE publish_month={max_year_month}"
    SQL=f"{SQL} AND satellite='{satellite}'"
    SQL=f"{SQL} GROUP BY satellite, path_row, view_date order by view_date ASC"
    
    return SQL

  def __lastMonthClosed(self):
    """
    Is the last month closed?

    Get the previous month reference based in the previous date from download control file and
    make difference with the current month. If the result is 2, so we have the last closed month.
    """
    # if no have previous month, or bypass check is enable, so continue
    forward=True

    if self.EVERY_DAY=='no' and self.FORCE_YEAR_MONTH=='no' and self.PREVIOUS_MONTH:
      previous_date=datetime.strptime(str(self.PREVIOUS_MONTH),'%Y-%m-%d').date()
      current_date=datetime.today().date()
      mm=current_date.month if current_date.year==previous_date.year else current_date.month+12
      forward=bool(mm-previous_date.month==2)

    return forward
  
  def __getCurrentYearMonth(self):
    """
    Define the current year and month reference used to download cmask data
    """
    publish_month=year_month=None

    if self.FORCE_YEAR_MONTH=='no':
      publish_month=datetime.today().strftime('%Y-%m-01') # to write on control file
      year_month=datetime.today().strftime('%Y_%m')
    else:
      publish_month=self.FORCE_YEAR_MONTH
      year_month=datetime.strptime(str(self.FORCE_YEAR_MONTH),'%Y-%m-%d').strftime('%Y_%m')

    return year_month, publish_month

  def __makeCmaskFileList(self):
    
    cmask_items=[]
    try:
      for sat_name in self.SATELLITES:
        sub_paths=self.__makeSubPathList(sat_name)
        sql=self.__buildQuery(sat_name)
        #SQL to get valid images of alerts at month
        cur = self.con.cursor()
        cur.execute("SET application_name = 'ETL - DETER CMask Task';")
        cur.execute(sql)
        resultset = cur.fetchall()

        for a_field in resultset:
          satellite = a_field[0] # from database
          path_row =  str(a_field[1])
          view_date = str(a_field[2])
          ano_mes_dia = view_date.replace('-', '_')
          anomesdia = view_date.replace('-', '')
          ano_mes = ano_mes_dia[0:7]
          
          aux = satellite.split("-")
          satellite = aux[0] + "_" +aux[1]
          pasta = aux[0] + aux[1]
          
          sensor = "AWFI"
          formato = "DRD"
          projecao = "UTM"
          
          if satellite == "AMAZONIA_1":
            projecao = "LCC"
          
          if satellite == "CBERS_4A" or satellite == "AMAZONIA_1":
            sensor = "WFI"
            formato = "RAW"
              
          tif_name = satellite + "_" + sensor + "_" + anomesdia + "_" + path_row + "_L4_CMASK_GRID_SURFACE.tif"
          name = satellite + "_" + sensor + "_" + formato + "_" + ano_mes_dia

          for sub_path in sub_paths:
            url = self.BASE_URL+"/" + pasta + "/" + ano_mes + "/" + sub_path + path_row + "_0/4_BC_" + projecao + "_WGS84/" + tif_name
            if name in sub_path:
              cmask_items.append({'tif_name':tif_name,'url':url})
    except Exception as error:
      cmask_items=[]
      raise error
    finally:
      cur.close()
      self.con.close()

    return cmask_items

  def __makeSubPathList(self, satellite):

    subpaths=[]
    satellite = satellite.replace('_', '')
    url="{0}/{1}/{2}".format(self.BASE_URL, satellite, self.YEAR_MONTH)
    # Getting page HTML through request
    page = requests.get(url)
    # Parsing content using beautifulsoup
    content_parsed = BeautifulSoup(page.content, 'html.parser')
    # Selecting all of the anchors with titles
    links = content_parsed.select("a")
    # ignore the first 5 anchors, that is control headers of page
    anchors = links[5:len(links)-1]
    pattern="/"
    for anchor in anchors:
      match = re.search(pattern, anchor.text)
      if(match):
        subpaths.append(anchor.text)
    
    return subpaths

  def __download(self):
    
    cmask_items=self.__makeCmaskFileList()
    self.found_items=0
    for cmask_item in cmask_items:
      try:
        headers=requests.head(cmask_item['url'])
        if headers.status_code==404:
          continue
        response = requests.get(cmask_item['url'])
        if response.ok:
          with open(f"{self.DATA_DIR}/{cmask_item['tif_name']}", 'wb') as f:
            f.write(response.content)
          self.found_items+=1
          print (cmask_item['tif_name'] + " found \n")
        else:
          print("Download fail with HTTP Error: {0}".format(response.status_code))
      except Exception as error:
        print (cmask_item['tif_name'] + " not found \n")
        print (error.msg)

  def __setMetadataResults(self):
    """
    Write download control file with date and number of files matched to use on next acquisition process
    """
    output_file="{0}/acquisition_data_control".format(self.DATA_DIR)
    # if the file already exists, truncate before write
    with open(output_file, 'w') as f:
      f.write("PREVIOUS_MONTH=\"{0}\"\n".format(self.PUBLISH_MONTH))
      f.write("found_items={0}".format(self.found_items))

  def __removeMetadataFile(self):
    """
    Delete the metadata file if there is an error trying to download the data
    """
    output_file="{0}/acquisition_data_control".format(self.DATA_DIR)
    if os.path.exists(output_file):
      os.remove(output_file)

  def __getPreviousMonthFromMetadata(self):
    """
    Read previous month from download control file
    """
    pm=None
    output_file="{0}/acquisition_data_control".format(self.DATA_DIR)
    if os.path.exists(output_file):
      with open(output_file) as f:
        lines=f.readlines()
        for line in lines:
          if line.split("=")[0]=="PREVIOUS_MONTH":
            pm=line.split("=")[1]
            pm=pm.strip()
            pm=pm.strip('"')
    return pm

  def get(self):
    try:
      if self.BIOME:
        self.__configForBiome()
        if self.__lastMonthClosed():
          self.__download()
          # used to write some information into a file that used for import data process
          self.__setMetadataResults()
      else:
        print("Wrong configurations")
    except Exception as error:
      down.__removeMetadataFile()
      print("There was an error when trying to download data.")
      print(error)

# end of class

# Call download for get data
down=DownloadCMASK()
down.get()