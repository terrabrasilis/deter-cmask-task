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
    # define the last year month variable
    self.LAST_YEAR_MONTH=None
    #
    # database params
    self.host=os.getenv("PGHOST", 'host')
    self.database=os.getenv("PGDB", 'database')
    self.port=os.getenv("PGPORT", '5432')
    self.user=os.getenv("PGUSER", 'user')
    self.password=os.getenv("PGPASSWORD", 'password')
    self.con=None # define class attribute
    #
    # the current biome name
    self.BIOME=os.getenv("TARGET_BIOME", 'amazonia')
    #
    # used to force one specific year_month to download
    self.FORCE_YEAR_MONTH=os.getenv("FORCE_YEAR_MONTH", 'no')
    # validation FORCE_YEAR_MONTH entry
    try:
      if self.FORCE_YEAR_MONTH!='no':
        # If we use a forced year/month (FORCE_YEAR_MONTH=YYYY-MM-01), so, use as the LAST_YEAR_MONTH;
        self.LAST_YEAR_MONTH=f"{(datetime.strptime(str(self.FORCE_YEAR_MONTH),'%Y-%m-%d')).strftime('%Y-%m')}-01"
    except Exception as error:
      self.FORCE_YEAR_MONTH='no'
      print("Variable FORCE_YEAR_MONTH is wrong, Set to default 'no'")
      print(f"Exception error message: {str(error)}")
    #
    # used to skip checking "if the last month is closed" and the flow is forced to happen every day.
    self.EVERY_DAY=os.getenv("EVERY_DAY", 'no') if self.FORCE_YEAR_MONTH=='no' else 'no'
    # validation EVERY_DAY entry
    if self.EVERY_DAY!='yes':
      self.EVERY_DAY='no'

  def __configForBiome(self):
    """
    Used to set the specific values of job parameters per each biome.
    """
    # define the base directory to store downloaded data
    self.DATA_DIR="{0}/{1}".format(self.DIR,self.BIOME)
    # create the output directory if it not exists
    os.makedirs(self.DATA_DIR, exist_ok=True)
    # try read previous month from control file
    self.PREVIOUS_YEAR_MONTH=self.__getPreviousYearMonthFromMetadata()
    # try read the last closed month from current deter table of the biome database
    self.__getLastClosedMonth()

  def __getImagesInformation(self, satellite:str):
    """
    Build and execute the SQL to get valid images of alerts at month.

    Mandatory parameters:
    -----------------------------
    :param:satellite: The valid name of satellite in DETER database.
    """

    satellite = satellite.replace('_', '-')

    sql=f"SELECT satellite, path_row, view_date"
    sql=f"{sql} FROM cloud.deter_current"
    sql=f"{sql} WHERE publish_month='{self.LAST_YEAR_MONTH}'::date"
    sql=f"{sql} AND satellite='{satellite}'"
    sql=f"{sql} GROUP BY satellite, path_row, view_date order by view_date ASC"

    resultset=self.__getData(sql)
    
    return resultset

  def __getLastClosedMonth(self):
    """
    Get the latest closed month from the database, used to read the satellite list,
    pathrows and image date and compose the CMASK image names.

    If we has a valid FORCE_YEAR_MONTH env var, use that as LAST_YEAR_MONTH
    """
    if self.LAST_YEAR_MONTH is None:
      sql = """
      SELECT MAX(publish_month)::text FROM cloud.deter_current
      WHERE view_date<=((SELECT MAX(publish_month) FROM cloud.deter_current)::date - interval '1 day')::date
      """
      resultset=self.__getData(sql)
      if resultset is not None:
        self.LAST_YEAR_MONTH=str(resultset[0][0])

  def __continue(self):
    """
    Proceed to download?

    Define whether we need to continue, respecting the following priority rules:
     - If bypass checking is enabled (EVERY_DAY=='yes') and the last(1) year/month exists, continue, otherwise, next rule;
     - Compare the last(1) year/month with the previous(2) year/month, if it's different, then continue, otherwise stop.

    (1) The last year/month is read from database. See the __getLastClosedMonth function.
    (2) The previous year/month is read* from download control file (acquisition_data_control) using the PREVIOUS_MONTH key.
    * if there is no previous year/month, we assume that previous download jobs were never run, so continue.
    """
    bypass=self.EVERY_DAY=='yes' and self.LAST_YEAR_MONTH is not None

    if not bypass and self.LAST_YEAR_MONTH is not None and self.PREVIOUS_YEAR_MONTH is not None:
      lym=datetime.strptime(str(self.LAST_YEAR_MONTH),'%Y-%m-%d')
      pym=datetime.strptime(str(self.PREVIOUS_YEAR_MONTH),'%Y-%m-%d')
      bypass=lym>pym
    
    return bypass

  def __getData(self, sql:str):

    resultset=cur=None
    # if connected, get the cursor
    if self.con is None or self.con.closed>0:
      # make connection with db based
      self.con = psycopg2.connect(host=self.host, port=self.port, database=self.database, user=self.user, password=self.password)

    try:
      cur = self.con.cursor()
      cur.execute("SET application_name = 'ETL - DETER CMask Task';")
      cur.execute(sql)
      resultset = cur.fetchall()
    except Exception as error:
      print("Failure when exec query on database")
      print(f"Exception error message: {str(error)}")
      resultset=None
      raise error

    return resultset

  def __closeResources(self):
    # closed==0 is code for connected. See psycopg2 docs: https://www.psycopg.org/docs/connection.html#connection.closed
    if self.con is not None and self.con.closed==0:
      self.con.close()

  def __makeCmaskFileList(self):
    
    cmask_items=[]
    try:
      for sat_name in self.SATELLITES:
        sub_paths=self.__makeSubPathList(sat_name)
        resultset=self.__getImagesInformation(sat_name)
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

    return cmask_items

  def __makeSubPathList(self, satellite):

    subpaths=[]
    satellite = satellite.replace('_', '')
    year_month=datetime.strptime(str(self.LAST_YEAR_MONTH),'%Y-%m-%d').strftime('%Y_%m')
    url="{0}/{1}/{2}".format(self.BASE_URL, satellite, year_month)
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
        print(f"Exception error message: {str(error)}")
        raise error

  def __setMetadataResults(self):
    """
    Write download control file with year/month (formated as YYYY-MM-01)
    and number of files matched to use on next acquisition process
    """
    output_file="{0}/acquisition_data_control".format(self.DATA_DIR)
    # if the file already exists, truncate before write
    with open(output_file, 'w') as f:
      f.write("PREVIOUS_MONTH=\"{0}\"\n".format(self.LAST_YEAR_MONTH))
      f.write("found_items={0}".format(self.found_items))

  def __getPreviousYearMonthFromMetadata(self):
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
        if self.__continue():
          self.__download()
          # used to write some information into a file that used for import data process
          self.__setMetadataResults()
      else:
        print("Wrong configurations")
    except Exception as error:
      print("There was an error when trying to download data.")
      print(f"Exception error message: {str(error)}")
    finally:
      self.__closeResources()

# end of class

# Call download for get data
down=DownloadCMASK()
down.get()