# tabula 
from multiprocessing.sharedctypes import Value
from tabula import read_pdf
from tabulate import tabulate

# pdf plumber
import requests
from io import BytesIO
import pdfplumber

# data analysis
import numpy as np
import pandas as pd
import re
import csv

# currency conversion
import converter

"""
*************************************
Pull Single Quarter Data from Company
*************************************
"""

def pull(url, year, quarter, company):
  """
  Selects correct pull function.
  """
  if company == 'tsmc':
    return pull_tsmc(year, quarter, url)
  elif company == 'smic':
    return pull_smic(year, quarter, url)
  elif company == 'umc':
    return pull_umc(year, quarter, url)
  elif company == 'gf':
    return pull_gf(year, quarter, url)


"""
**********************************************
Taiwan Semiconductor Manufacturing Corporation
**********************************************
"""

def pull_tsmc(year, quarter, url):
  """
  Pulls a single quarter's data for TSMC and returns as a dictionary.
  """
  data_tsmc = []
  try:
    tsmc_dfs = parse_tsmc(url)
    dict_geo_options_tsmc = {'North America':'NORAM', 'Asia Pacific':'ASIAPAC'}
    conv = converter.Converter()

    try:
      tsmc_rev_converted = get_rev_tsmc(year, quarter, url)
      aggregated_rev = {'company': 'TSMC', 'year': year, 'quarter': quarter, 'metric': 'rev', 'sub-metric': '','value': tsmc_rev_converted}
      data_tsmc.append(aggregated_rev)
    except:
      print("rev error")

    try:
      tsmc_inv = tsmc_dfs.get('inv')
      tsmc_inv_value = tsmc_inv.iat[0,1]
      tsmc_inv_value_commaless = tsmc_inv_value.replace(",","")
      tsmc_inv_millions = float(tsmc_inv_value_commaless) * 1000
      tsmc_inv_converted = conv.twd_usd(tsmc_inv_millions, year, quarter)
      aggregated_inv = {'company': 'TSMC', 'year': year, 'quarter': quarter, 'metric': 'inv', 'value': tsmc_inv_converted}
      data_tsmc.append(aggregated_inv)
    except:
      print("inv error")
    
    try:
      tsmc_capex = tsmc_dfs.get('capex')
      tsmc_capex_value = tsmc_capex.iat[1,1]
      tsmc_capex_value_commaless = tsmc_capex_value.replace(",","")
      tsmc_capex_millions = float(tsmc_capex_value_commaless) * 1000
      tsmc_capex_converted = conv.twd_usd(tsmc_capex_millions, year, quarter)
      aggregated_capex = {'company': 'TSMC', 'year': year, 'quarter': quarter, 'metric': 'capex', 'value': tsmc_capex_converted}
      data_tsmc.append(aggregated_capex)
    except:
      print("capex error")
                
    try:
      tsmc_geo = tsmc_dfs.get('geo')
      for _, row in tsmc_geo.iterrows():
          sub_geo = row[0]
          sub_geo_value = row[1]
          sub_geo_no_percent = sub_geo_value.replace("%","")
          if sub_geo in dict_geo_options_tsmc:
              sub_geo = dict_geo_options_tsmc.get(sub_geo)
          aggregated_geo = {'company': 'TSMC', 'year': year, 'quarter': quarter, 'metric': 'rev_geo', 'sub-metric' : sub_geo, 'value': sub_geo_no_percent}
          data_tsmc.append(aggregated_geo)
    except:
      print("geo error")

    try:
      tsmc_seg = tsmc_dfs.get('segment')
      for _, row in tsmc_seg.iterrows():
          sub_seg = row[0]
          sub_seg_value = row[1]
          sub_seg_no_percent = sub_seg_value.replace("%","")
          aggregated_seg = {'company': 'TSMC', 'year': year, 'quarter': quarter, 'metric': 'rev_seg', 'sub-metric' : sub_seg, 'value': sub_seg_no_percent}
          data_tsmc.append(aggregated_seg)
    except:
      print("seg error")

    try:
      tsmc_tech = tsmc_dfs.get('tech')
      for _, row in tsmc_tech.iterrows():
          sub_tech = row[0]
          sub_tech_value = row[1]
          sub_tech_no_percent = sub_tech_value.replace("%","")
          aggregated_tech = {'company': 'TSMC', 'year': year, 'quarter': quarter, 'metric': 'rev_tech', 'sub-metric' : sub_tech, 'value': sub_tech_no_percent}
          data_tsmc.append(aggregated_tech)
    except:
      print("tech error")

  except Exception as err:
    print(year, quarter, url)
    print(err)

  return data_tsmc

def get_rev_tsmc(year, quarter, url):
  tsmc_rev_converted = 0
  try:
    rq = requests.get(url)
    pdf = pdfplumber.open(BytesIO(rq.content))
    text = ""
    text += pdf.pages[0].extract_text()
    revenue_regex = "\$\d+,*\d*\.*\d*"
    revenue = re.findall(f"{revenue_regex}", text)[0]
    revenue_no_dollar_sign = revenue.replace("$","")
    revenue_no_comma = revenue_no_dollar_sign.replace(",","")
    revenue_num_millions = float(revenue_no_comma) * 1000
    conv = converter.Converter()
    tsmc_rev_converted = conv.twd_usd(revenue_num_millions, year, quarter)
  except:
    print(year, quarter, url)
  return tsmc_rev_converted

def parse_tsmc(url):
  """
  Pulls all TSMC informaiton from a URL. Missing pieces will have None value.
  """
  print(f'url: {url}')
  rq = requests.get(url)
  pdf = pdfplumber.open(BytesIO(rq.content))
  tsmc_text = ""
  for i in range(5):
      tsmc_text += pdf.pages[i].extract_text()
  tech_df = clean_tsmc_tech_robust(tsmc_text)
  geo_df = clean_tsmc_geo(tsmc_text)
  try:
    capex_df = extract_tsmc_capex(pdf)
  except ValueError:
    capex_df = None
    print("Capex failed for " + url)
  try:
    inv_df = extract_tsmc_inv(pdf)
  except IndexError:
    inv_df = None
    print("Inv failed for " + url)
  try: 
      platform_df = clean_tsmc_platform(tsmc_text)
  except IndexError:
      platform_df = None
      print("Platform df failed for " + url)
  try: 
      seg_df = clean_tsmc_seg(tsmc_text)
  except IndexError:
      seg_df = None
      print("Segment df failed for " + url)
  return {
    'tech': tech_df,
    'platform': platform_df,
    'segment': seg_df,
    'geo': geo_df,
    'capex' : capex_df,
    'inv' : inv_df
  }

def clean_tsmc_tech_robust(tsmc_text):
  """
  Cleans TSMC's tech dataframe.
  """
  digits = "\s+(\dQ\d+)\s+(\dQ\d+)\s+(\dQ\d+)"
  techCols = np.asarray(re.findall(f"(Wafer (?:Revenue|Rev\.) by Technology|By Application){digits}", tsmc_text)[0])
  techArray = []
  digit_re = "\d+(?:u|n)m"
  slash = "\d+(?:\.\d+)?\/\d+(?:\.\d+)?(?:u|n)m"
  above = "\d+(?:\.\d+)?(?:u|n)m\s+and\s+above"
  plus = "\d+(?:\.\d+)?(?:u|n)m\+"
  numbers = "\s(\d+%)\s(\d+%)\s(\d+%)"
  techRegex = f"({digit_re}|{slash}|{above}|{plus}){numbers}"
  for i in re.finditer(techRegex, tsmc_text):
      techArray.append(list(i.groups()))
  techDF = pd.DataFrame(techArray, columns=techCols)
  ser = techDF.iloc[:, 0]
  try:
      stop_index = ser[(ser.str.match(above) == True)].index[0] + 1
  except IndexError:
      stop_index = ser[(ser.str.match(plus) == True)].index[0] + 1
  techDF = techDF.iloc[:stop_index, :]
  return techDF
  
def clean_tsmc_platform(tsmc_text):
  """
  Cleans TSMC's platform dataframe.
  """
  digits = "\s+(\d+%)\s+(\d+%)\s+(\d+%)"
  quarters = "\s+(\d+Q\d+)\s+(\d+Q\d+)\s+(\d+Q\d+)"
  segCols = np.asarray(re.findall(f"(Net Revenue by Platform){quarters}", tsmc_text)[0])
  smartphone = np.asarray(re.findall(f"(Smartphone){digits}", tsmc_text)[0])
  hpc = np.asarray(re.findall(f"(High Performance Computing){digits}", tsmc_text)[0])
  iot = np.asarray(re.findall(f"(Internet of Things){digits}", tsmc_text)[0])
  auto = np.asarray(re.findall(f"(Automotive){digits}", tsmc_text)[0])
  consumer = np.asarray(re.findall(f"(Digital Consumer Electronics){digits}", tsmc_text)[0])
  others = np.asarray(re.findall(f"(Others){digits}", tsmc_text)[0])
  tsmcPlat = np.array([smartphone, hpc, iot, auto, consumer, others])
  platDF = pd.DataFrame(tsmcPlat, columns=segCols)
  return platDF

def clean_tsmc_seg(tsmc_text):
  """
  Cleans TSMC's segment dataframe.
  """
  digits = "\s+(\d+%)\s+(\d+%)\s+(\d+%)"
  quarters = "\s+(\d+Q\d+)\s+(\d+Q\d+)\s+(\d+Q\d+)"
  segCols = np.asarray(re.findall(f"((?:Wafer|Net) (?:Revenue|Rev\.|Sales) by Application|By Application|By Customer Type){quarters}", tsmc_text)[0])
  computer = np.asarray(re.findall(f"(Computer){digits}", tsmc_text)[0])
  comm = np.asarray(re.findall(f"(Communication){digits}", tsmc_text)[0])
  consumer = np.asarray(re.findall(f"(Consumer){digits}", tsmc_text)[0])
  indus = np.asarray(re.findall(f"(Industrial/Standard){digits}", tsmc_text)[0])
  tsmcSeg = np.array([computer, comm, consumer, indus])
  segDF = pd.DataFrame(tsmcSeg, columns=segCols)
  return segDF

def clean_tsmc_geo(tsmc_text):
  """
  Cleans TSMC's geo dataframe.
  """
  umcRegions = []
  digits = "\s+(\d+%)\s+(\d+%)\s+(\d+%)"
  regionCols = np.asarray(re.findall(r"((?:Net|Wafer) (?:Revenue|Rev\.) by Geography|By Geography)\s+(\d+Q\d+)\s+(\d+Q\d+)\s+(\d+Q\d+)", tsmc_text)[0])
  NorthAm = np.asarray(re.findall(f"(North America){digits}", tsmc_text)[0])
  umcRegions.append(NorthAm)
  China = np.asarray(re.findall(f"(China){digits}", tsmc_text)[0])
  umcRegions.append(China)
  try:
      EMEA = np.asarray(re.findall(f"(EMEA){digits}", tsmc_text)[0])
      umcRegions.append(EMEA)
  except IndexError:
      pass
  try:
      europe = np.asarray(re.findall(f"(Europe){digits}", tsmc_text)[0])
      umcRegions.append(europe)
  except IndexError:
      pass
  try: 
      APAC = np.asarray(re.findall(f"(Asia Pacific){digits}", tsmc_text)[0])
      umcRegions.append(APAC)
  except IndexError:
      pass
  Japan = np.asarray(re.findall(f"(Japan){digits}", tsmc_text)[0])
  umcRegions.append(Japan)
  geoDF = pd.DataFrame(umcRegions, columns=regionCols)
  return geoDF

def extract_tsmc_capex(pdf):
  """
  Extracts capital expenditures from TSMC text pdf.
  """
  text = [p.extract_text() for p in pdf.pages if 'V. CapEx' in p.extract_text()][0] # find page with capex
  capex_text = text.split('V. CapEx')[1] # split to part with capex
  quarters = sorted(set(re.findall('\dQ\d{2}', capex_text)), key=lambda x: x[2:] + x[:2]) # find quarters mentioned
  capex = re.findall(' (\d+\.\d{2})', capex_text)[:len(quarters)] # extract capex numbers
  return pd.DataFrame({'quarter':quarters, "capex":capex}) # return as df


def extract_tsmc_inv(pdf):
  """
  Extracts inventory from TSMC text pdf.
  """
  text = [p.extract_text() for p in pdf.pages if 'Inventories' in p.extract_text()][0] # find page with capex
  quarters = re.search('(\dQ\d{2})\s*(\dQ\d{2})\s*(\dQ\d{2})', text).groups()
  inventory = re.search('Inventories\s*(\d+\.\d+)\s*(\d+\.\d+)\s*(\d+\.\d+)\s', text).groups()
  return pd.DataFrame({'quarter':quarters, "inv":inventory}) # return as df


"""
*****************************************************
Semiconductor Manufacturing International Corporation
*****************************************************
"""

def pull_smic(year, quarter, url):
  """
  Pulls a single quarter's data for SMIC and returns as a dictionary.
  """
  data_smic = []
  try:
    year_quarter = '{}Q{}'.format(year, quarter)
    smic_dfs = parse_smic(url, year_quarter)
    dict_geo_options_smic = {'North America(1)':'NORAM', 'United States':'US', 
    'Mainland China and Hong Kong':'CHINAHK','Chinese Mainland and Hong Kong, China':'CHINAHK', 
    'Eurasia(2)':'EURASIA', 'North America':'NORAM', 'Eurasia':'EURASIA'}

    try:
      revenue_num = get_rev_smic(year, quarter, url)
      aggregated_rev = {'company': 'SMIC', 'year': year, 'quarter': quarter, 'metric': 'rev', 'value': revenue_num}
      data_smic.append(aggregated_rev)
    except:
      print("rev error")

    try:
      smic_inv = smic_dfs.get('inv')
      inv_value_old = smic_inv.iat[0,1]
      inv_value_converted = inv_value_old[:len(inv_value_old) - 4]
      inv_value_converted_commaless = inv_value_converted.replace(",","")
      aggregated_inv = {'company': 'SMIC', 'year': year, 'quarter': quarter, 'metric': 'inv', 'value': inv_value_converted_commaless}
      data_smic.append(aggregated_inv)
    except:
      print("inv error")
    
    try:
      smic_capex = smic_dfs.get('capex')
      smic_capex_value = smic_capex.iat[0,1]
      smic_capex_value_commaless = smic_capex_value.replace(",","")
      aggregated_capex = {'company': 'SMIC', 'year': year, 'quarter': quarter, 'metric': 'capex', 'value': smic_capex_value_commaless}
      data_smic.append(aggregated_capex)
    except:
      print("capex error")
    
    try:
      smic_geo = smic_dfs.get('geo')
      for _, row in smic_geo.iterrows():
          sub_geo = row[0]
          sub_geo_value = row[1]
          sub_geo_no_percent = sub_geo_value.replace("%","")
          if sub_geo in dict_geo_options_smic:
              sub_geo = dict_geo_options_smic.get(sub_geo)
          aggregated_geo = {'company': 'SMIC', 'year': year, 'quarter': quarter, 'metric': 'rev_geo', 'sub-metric' : sub_geo, 'value': sub_geo_no_percent}
          data_smic.append(aggregated_geo)
    except:
      print("geo error")

    try:
      smic_seg = smic_dfs.get('segment')
      for _, row in smic_seg.iterrows():
          sub_seg = row[0]
          sub_seg_value = row[1]
          sub_seg_no_percent = sub_seg_value.replace("%","")
          aggregated_seg = {'company': 'SMIC', 'year': year, 'quarter': quarter, 'metric': 'rev_seg', 'sub-metric' : sub_seg, 'value': sub_seg_no_percent}
          data_smic.append(aggregated_seg)
    except:
      print("seg error")

    try:
      smic_tech = smic_dfs.get('tech')
      for _, row in smic_tech.iterrows():
          sub_tech = row[0]
          sub_tech_value = row[1]
          sub_tech_no_percent = sub_tech_value.replace("%","")
          aggregated_tech = {'company': 'SMIC', 'year': year, 'quarter': quarter, 'metric': 'rev_tech', 'sub-metric' : sub_tech, 'value': sub_tech_no_percent}
          data_smic.append(aggregated_tech)
    except:
      print("tech error")

  except Exception as err:
    print(year, quarter, url)
    print(err)

  return data_smic

def get_rev_smic(year, quarter, url):
  revenue_num = 0
  try:
    rq = requests.get(url)
    pdf = pdfplumber.open(BytesIO(rq.content))
    text = ""
    text += pdf.pages[0].extract_text()
    revenue_regex = "\$\d+,*\d*\.*\d*"
    revenue = re.findall(f"{revenue_regex}", text)[0]
    revenue_no_dollar_sign = revenue.replace("$","")
    revenue_no_comma = revenue_no_dollar_sign.replace(",","")
    revenue_num = float(revenue_no_comma)
  except:
    print(year, quarter, url)
  return revenue_num

def parse_smic(url, year_quarter):
  """
  Pulls all SMIC information from a URL. Missing pieces will have None value.
  """
  dfs = read_pdf(url, pages=[5, 6, 7, 8, 9])
  df = [df for df in dfs if 'Revenue Analysis' in df.columns][0]
  
  rq = requests.get(url)
  pdf = pdfplumber.open(BytesIO(rq.content))
  smic_dfs = {}
  try:
    inv_df = extract_smic_inv(pdf)
    smic_dfs['inv'] = inv_df
  except:
    print("inv broken")
  
  try:
    capex_df = extract_smic_capex(pdf, year_quarter)
    smic_dfs['capex'] = capex_df
  except:
    print("capex broken")

  indices = df[df.iloc[:, 0].str.contains(r"By Geography|By Service Type|By Application|By Technology")].index.tolist()
  
  try:
    geo_df = promote_row(df.iloc[indices[0]:indices[1], :])
    smic_dfs['geo'] = geo_df
  except:
    print("geo broken")
  try:
    service_df = promote_row(df.iloc[indices[1]:indices[2]-1, :])
    smic_dfs['service'] = service_df
  except:
    print("service broken")
  try:
    segment_df = promote_row(df.iloc[indices[2]:indices[3], :])
    smic_dfs['segment'] = segment_df
  except:
    print('seg broken')
  try:
    tech_df = promote_row(df.iloc[indices[3]:, :])
    smic_dfs['tech'] = tech_df
  except:
    print("tech broken")
  
  return smic_dfs

def promote_row(df):
  """
  Helper function.
  """
  df.columns = df.iloc[0]
  df = df[1:].reset_index(drop=True)
  df.index.name = None
  return df

def extract_smic_inv(pdf):
  """
  Extracts inventory from SMIC text pdf.
  """
  text = ""
  if len(pdf.pages) > 12:
      for i in range(5,13):
          text += pdf.pages[i].extract_text()
  else:
      for i in range(5,10):
          text += pdf.pages[i].extract_text()
  digits = "\s+(\d+,?\d+,?\d+)\s+(\d+,?\d+,?\d+)"
  columnHeaders = "\s+(\dQ\d+)\s+(\dQ\d+)"
  invCols = list(re.findall(f"(Amounts in US\$ thousands){columnHeaders}", text)[0])
  inv = np.asarray(re.findall(f"(Inventories){digits}", text)[0])
  curr_assets = np.asarray(re.findall(f"(Total current assets){digits}", text)[0])
  curr_liabilities = np.asarray(re.findall(f"(Total current liabilities){digits}", text)[0])
  smicSeg = np.array([inv, curr_assets, curr_liabilities])
  segDF = pd.DataFrame(smicSeg, columns=invCols)
  return segDF

def extract_smic_capex(pdf, year_quarter):
  """
  Extracts capex from a SMIC text pdf. 
  """
  text = ""
  if len(pdf.pages) > 12:
      for i in range(5,13):
          text += pdf.pages[i].extract_text()
  else:
      for i in range(5,10):
          text += pdf.pages[i].extract_text()
  # special case for table
  if year_quarter == '12Q4':
      capex_start = text.find('Capex Summary')
      quarter_text = re.split('Capital expenditures for', text[capex_start:])[0]
      quarters = re.findall('\dQ\d\d', quarter_text) or re.findall('\d\dQ\d', quarter_text)
      capex_text = re.split('Capital expenditures', quarter_text)[1]
      capex = re.findall('([\d\.,]+)\s', capex_text)
      capex = [round(float(cpx.replace(',',''))/1000, 1) for cpx in capex]
  else:
      capex_start = text.find('Capital expenditures for')
      if capex_start == -1: capex_start = text.find('Capital expenditures were')
      target_text = re.split('\.\s', text[capex_start:])[0]
      quarters = re.findall('\d[QH]\d\d', target_text)
      if not quarters:
        quarters = re.findall('\d\dQ\d', target_text)
        quarters = [q[:2] + q[2:] for q in quarters]
      quarters = [q.replace('H', 'Q') for q in quarters]
      capex = re.findall('\$([\d\.,]+) million', target_text) or re.findall('\$([\d\.,]+)M', target_text)
  return pd.DataFrame({'quarter':quarters, "capex":capex})


"""
***********************************
United Microelectronics Corporation
***********************************
"""

def pull_umc(year, quarter, url):
  """
  Pulls a single quarter's data for UMC and returns as a dictionary.
  """
  data_umc = []
  try:
    umc_dfs = parse_umc(url)
    dict_geo_options_umc = {'North America':'NORAM', 'Asia Pacific':'ASIAPAC'}
    year_quarter = '{}Q{}'.format(year, quarter)
    conv = converter.Converter()

    try:            
      umc_rev = get_rev_umc(year, quarter, url)
      aggregated_rev = {'company': 'UMC', 'year': year, 'quarter': quarter, 'metric': 'rev', 'value': umc_rev}
      data_umc.append(aggregated_rev)
    except:
      print(year, quarter, url)
    
    try:
      umc_geo = umc_dfs.get('geo')
      for _, row in umc_geo.iterrows():
          sub_geo = row[0]
          sub_geo_value = row[1]
          sub_geo_no_percent = sub_geo_value.replace("%","")
          if sub_geo in dict_geo_options_umc:
              sub_geo = dict_geo_options_umc.get(sub_geo)
          aggregated_geo = {'company': 'UMC', 'year': year, 'quarter': quarter, 'metric': 'rev_geo', 'sub-metric' : sub_geo, 'value': sub_geo_no_percent}
          data_umc.append(aggregated_geo)
    except:
      print(year, quarter, url)

    try:
      umc_tech = umc_dfs.get('tech')
      for _, row in umc_tech.iterrows():
          sub_tech = row[0]
          sub_tech_value = row[1]
          sub_tech_no_percent = sub_tech_value.replace("%","")
          aggregated_tech = {'company': 'UMC', 'year': year, 'quarter': quarter, 'metric': 'rev_tech', 'sub-metric' : sub_tech, 'value': sub_tech_no_percent}
          data_umc.append(aggregated_tech)
    except:
      print(year, quarter, url)

    # umc_seg = umc_dfs.get('segment')
    # for _, row in umc_seg.iterrows():
    #     sub_seg = row[0]
    #     sub_seg_value = row[1]
    #     sub_seg_no_percent = sub_seg_value.replace("%","")
    #     aggregated_seg = {'company': 'UMC', 'year': year, 'quarter': quarter, 'metric': 'rev_seg', 'sub-metric' : sub_seg, 'value': sub_seg_no_percent}
    #     data_umc.append(aggregated_seg)
    
    # currently commented out because umc_seg scraper scrapes wrong table
    try:
      umc_inv = umc_dfs.get('inv')
      umc_inv_value = umc_inv.iat[0,1]
      umc_inv_value_commaless = umc_inv_value.replace(",","")
      umc_inv_millions = float(umc_inv_value_commaless) * 1000
      umc_inv_converted = conv.twd_usd(umc_inv_millions, year, quarter)
      aggregated_inv = {'company': 'UMC', 'year': year, 'quarter': quarter, 'metric': 'inv', 'value': umc_inv_converted}
      data_umc.append(aggregated_inv)
    except:
      print(year, quarter, url)

    try:
      umc_capex = umc_dfs.get('capex')
      umc_capex_value = umc_capex.iat[0,1]
      umc_capex_value_commaless = umc_capex_value.replace(",","")
      umc_capex_value_clean1 = umc_capex_value_commaless.replace("(","")
      umc_capex_value_clean2 = umc_capex_value_clean1.replace(")","")
      umc_capex_value_float = float(umc_capex_value_clean2)
      umc_capex_converted = conv.twd_usd(umc_capex_value_float, year, quarter)
      aggregated_capex = {'company': 'UMC', 'year': year, 'quarter': quarter, 'metric': 'capex', 'value': umc_capex_converted}
      data_umc.append(aggregated_capex)
    except:
      print(year, quarter, url)

  except Exception as err:
    print(year, quarter, url)
    print(err)

  return data_umc

def get_rev_umc(year, quarter, url):
  revenue_num = 0
  try:
    rq = requests.get(url, verify=False)
    pdf = pdfplumber.open(BytesIO(rq.content))
    text = ""
    text += pdf.pages[0].extract_text()
    revenue_regex = "US\$\d+,*\d*\.*\d*"
    revenue = re.findall(f"{revenue_regex}", text)[0]
    revenue_no_dollar_sign = revenue.replace("US$","")
    revenue_no_comma = revenue_no_dollar_sign.replace(",","")
    revenue_num = float(revenue_no_comma)
    if revenue_num < 10:
      revenue_num *= 1000
  except:
    print(year, quarter, url)
  return revenue_num


def parse_umc(url):
  """
  Pulls all available UMC information from a URL. Missing pieces will have None value.
  """
  rq = requests.get(url, verify=False)
  pdf = pdfplumber.open(BytesIO(rq.content))
  umc_text = ""
  umc_dict = {}
  for i in range(10):
      umc_text += pdf.pages[i].extract_text()
  try:
    tech_df = clean_umc_tech_robust(umc_text)
    umc_dict['tech'] = tech_df
  except:
    print("tech_df error")
  try:
    segment_df = clean_umc_seg(umc_text)
    umc_dict['segment'] = segment_df
  except:
    print("segment df error")
  try:
    geo_df = clean_umc_geo(umc_text)
    umc_dict['geo'] = geo_df
  except:
    print("geo_df error")
  try:
    capex_df = clean_umc_capex(umc_text)
    umc_dict['capex'] = capex_df
  except:
    print("capex_df error")
  try:
    inv_df = clean_umc_inv(umc_text)
    umc_dict['inv'] = inv_df
  except:
    print("inv_df error")
  """
  return {
    'tech': tech_df,
    'segment': segment_df,
    'geo': geo_df,
    'inv': inv_df,
    'capex' : capex_df
    }
  """
  return umc_dict

def clean_umc_tech_robust(umc_text):
  """
  Cleans UMC's tech dataframe.
  """
  digits = "\s+(\dQ\d{2})\s+(\dQ\d{2})\s+(\dQ\d{2})\s+(\dQ\d{2})\s+(\dQ\d{2})"
  techCols = np.asarray(re.findall(f"(Geometry){digits}", umc_text)[0])
  techArray = []
  digit_re = "\d+[\.]?\d*[nu]m\s*and\s*above"
  inequality = "\d+[\.]?\d*[nu]m\s*<x<=\d+[\.]?\d*[nu]m"
  below = "\d+[\.]?\d*[nu]m\s*and\s*below"
  numbers = "\s+(\d+%)\s+(\d+%)\s+(\d+%)\s+(\d+%)\s+(\d+%)"
  techRegex = f"({digit_re}|{inequality}|{below}){numbers}"
  for i in re.finditer(techRegex, umc_text):
      techArray.append(list(i.groups()))
  techDF = pd.DataFrame(techArray, columns=techCols)
  return techDF

def clean_umc_seg(umc_text):
  """
  Cleans UMC's segment dataframe.
  """
  digits = "\s+(\d+%)\s+(\d+%)\s+(\d+%)\s+(\d+%)\s+(\d+%)"
  quarters = "\s+(\dQ\d{2})\s+(\dQ\d{2})\s+(\dQ\d{2})\s+(\dQ\d{2})\s+(\dQ\d{2})"
  segCols = np.asarray(re.findall(f"(Customer Type){quarters}", umc_text)[0])
  Fabless = np.asarray(re.findall(f"(Fabless){digits}", umc_text)[0])
  IDM = np.asarray(re.findall(f"(IDM){digits}", umc_text)[0])
  umcSeg = np.array([Fabless, IDM])
  segDF = pd.DataFrame(umcSeg, columns=segCols)
  return segDF

def clean_umc_geo(umc_text):
  """
  Cleans UMC's geography dataframe.
  """
  regionCols = np.asarray(re.findall(r"(Region)\s+(\dQ\d{2})\s+(\dQ\d{2})\s+(\dQ\d{2})\s+(\dQ\d{2})\s+(\dQ\d{2})", umc_text)[0])
  NorthAm = np.asarray(re.findall(r"(North America)\s+(\d+%)\s+(\d+%)\s+(\d+%)\s+(\d+%)\s+(\d+%)", umc_text)[0])
  APAC = np.asarray(re.findall(r"(Asia Pacific)\s+(\d+%)\s+(\d+%)\s+(\d+%)\s+(\d+%)\s+(\d+%)", umc_text)[0])
  Europe = np.asarray(re.findall(r"(Europe)\s+(\d+%)\s+(\d+%)\s+(\d+%)\s+(\d+%)\s+(\d+%)", umc_text)[0])
  Japan = np.asarray(re.findall(r"(Japan)\s+(\d+%)\s+(\d+%)\s+(\d+%)\s+(\d+%)\s+(\d+%)", umc_text)[0])
  umcRegions = np.array([NorthAm, APAC, Europe, Japan])
  geoDF = pd.DataFrame(umcRegions, columns=regionCols)
  return geoDF

def clean_umc_inv(umc_text):
  """
  Cleans UMC's inventory dataframe.
  """
  invCols = np.array(["Inventory"])
  quarters = "\s+(\dQ\d{2})\s+(\dQ\d{2})\s+(\dQ\d{2})"
  digits = "\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)"
  invCols = np.append(invCols,np.asarray(re.findall(f"(?:\(?Amount: NT\$ billion\)?){quarters}", umc_text)[0]))
  inv = list(re.findall(f"(Inventories, net){digits}", umc_text)[0])
  umcCapex = np.array([inv])
  capexDF = pd.DataFrame(umcCapex, columns=invCols)
  return capexDF

def clean_umc_capex(umc_text):
  """
  Cleans UMC's capex dataframe.
  """
  digits = "\s+(\(?\d+(?:,\d+)?\)?)\s+(\(?\d+(?:,\d+)?\)?)"
  invCols = ["Capex", "For 3-Month Period Ending Current Quarter", "For 3-Month Period Ending Last Year"]
  inv = list(re.findall(f"(Acquisition of PP&E){digits}", umc_text)[0])
  umcCapex = np.array([inv])
  capexDF = pd.DataFrame(umcCapex, columns=invCols)
  return capexDF

"""
****************
Global Foundries
****************
"""

def pull_gf(year, quarter, url):
  """
  Pulls a single quarter's data for GlobalFoundries and returns as a dictionary.
  """
  data_gf = []
  
  try:
    gf_dfs = parse_gf(url)

    revenue_num = get_rev_gf(year, quarter, url)
    aggregated_rev = {'company': 'Global Foundries', 'year': year, 'quarter': quarter, 'metric': 'rev', 'value': revenue_num}
    data_gf.append(aggregated_rev)
    
    gf_capex = gf_dfs.get('capex')
    gf_capex_value = gf_capex.iat[0,2]
    gf_capex_value_commaless = gf_capex_value.replace(",","")
    aggregated_capex = {'company': 'Global Foundries', 'year': year, 'quarter': quarter, 'metric': 'capex', 'value': gf_capex_value_commaless}
    data_gf.append(aggregated_capex)

    gf_inv = gf_dfs.get('inv')
    gf_inv_value = gf_inv.iat[0,2]
    gf_inv_value_commaless = gf_inv_value.replace(",","")
    aggregated_inv = {'company': 'Global Foundries', 'year': year, 'quarter': quarter, 'metric': 'inv', 'value': gf_inv_value_commaless}
    data_gf.append(aggregated_inv)
  
  except Exception as err:
    print(year, quarter, url)
    print(err)
  
  return data_gf

def get_rev_gf(year, quarter, url):
  revenue_num = 0
  try:
    rq = requests.get(url)
    pdf = pdfplumber.open(BytesIO(rq.content))
    text = ""
    text += pdf.pages[0].extract_text()
    revenue_regex = "\$\d+,*\d*\.*\d*"
    revenue = re.findall(f"{revenue_regex}", text)[0]
    revenue_no_dollar_sign = revenue.replace("$","")
    revenue_no_comma = revenue_no_dollar_sign.replace(",","")
    revenue_num = float(revenue_no_comma) * 1000
  except:
    print(year, quarter, url)
  return revenue_num

def parse_gf(url):
  """
  Pulls all GlobalFoundries information from a URL. Missing pieces will have None value.
  """
  rq = requests.get(url)
  pdf = pdfplumber.open(BytesIO(rq.content))
  gf_text = ""
  for i in range(5):
      gf_text += pdf.pages[i].extract_text()
  inv_df = extract_gf_inv(gf_text)
  capex_df = extract_gf_capex(gf_text)
  return {
    'inv': inv_df,
    'capex' : capex_df
  }

def extract_gf_inv(gf_text):
  """
  Extracts GlobalFoundries inventory from PDF text.
  """
  digits = "\s+\$?(\d+,?\d+)\s+\$?(\d+,?\d+)"
  columnHeaders = "\s+(\w+\s+\d+,\s+\d+)\s+(\w+\s+\d+,\s+\d+)"
  invCols = ["Inventory"] + list(re.findall(f"\(in \$M|\(in millions USD\){columnHeaders}", gf_text)[0])
  inv = np.asarray(re.findall(f"(Inventories){digits}", gf_text)[0])
  curr_assets = np.asarray(re.findall(f"(Current assets){digits}", gf_text)[0])
  total_assets = np.asarray(re.findall(f"(Total assets){digits}", gf_text)[0])
  umcSeg = np.array([inv, curr_assets, total_assets])
  segDF = pd.DataFrame(umcSeg, columns=invCols)
  return segDF

def extract_gf_capex(gf_text):
  """
  Extracts GlobalFoundries capex from PDF text.
  """
  digits = "\s+(\(?\$?\d+\)?)\s+(\(?\$?\d+\)?)"
  columnHeaders = "\s+(\w+\s+\d+,\s+\d+)\s+(\w+\s+\d+,\s+\d+)"
  invCols = ["Capex"] + list(re.findall(f"\(in \$M|\(in millions USD\){columnHeaders}", gf_text)[0])
  inv = list(re.findall(f"(Purchases of property, plant, equipment, and intangible assets){digits}", gf_text)[0])
  newInv = ["Asset Purchases"] + inv[1:]
  other_inv = np.asarray(re.findall(f"(Other) investing activities{digits}", gf_text)[0])
  net_cash = np.asarray(re.findall(f"(Net cash used) in investing activities{digits}", gf_text)[0])
  gfCapex = np.array([newInv, other_inv, net_cash])
  capexDF = pd.DataFrame(gfCapex, columns=invCols)
  return capexDF