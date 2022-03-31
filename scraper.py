# tabula 
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

"""
Taiwan Semiconductor Manufacturing Corporation
"""


def parse_tsmc(url):
  """
  Read TSMC quarterly management reports and extract revenue by technology, revenue by platform, revenue by geography, and capex.
  """
  cat_map = {'Wafer Revenue by Application': "", 'Wafer Revenue by Technology': "", 'Net Revenue by Geography': ""}
  # read PDF via tabula
  rev_dfs = read_pdf(url, pages=2)

  for i in range(len(rev_dfs)):
    for key in cat_map:
        inHeader = bool(re.search(key, rev_dfs[i].columns[0]))
        inColumn = bool(re.search(key, rev_dfs[i].iloc[:, 0].values[0]))
        if inHeader or inColumn:
          cat_map[key] = i

  tech_index = cat_map["Wafer Revenue by Technology"]
  segment_index = cat_map["Wafer Revenue by Application"]
  geo_index = cat_map["Net Revenue by Geography"]
  
  tech_df = clean_tsmc_tech(rev_dfs[tech_index])
  segment_df = clean_tsmc_segment(rev_dfs[segment_index])
  geo_df = clean_tsmc_geo(geo_index)  

  rq = requests.get(url)
  pdf = pdfplumber.open(BytesIO(rq.content))
  capex_df = extract_tsmc_capex(pdf)
  inv_df = extract_tsmc_inv(pdf)

  return {'tech':tech_df, 'segment':segment_df, 'geo': geo_df, 'capex':capex_df, 'inv':inv_df}

def clean_tsmc_tech(df):
  """
  Cleans TSMC's tech dataframe.
  """
  # if more tha two columns are unnamed:
  while not df.columns.str.contains('Net Revenue').any():
    df.columns = df.iloc[0]
    df = df[1:]


  # remove any other unnamed columns
  df = df.loc[:, df.columns.notna()]
  df = df.loc[:, df.columns.str.match(r'\dQ\d{2}') | df.columns.str.contains('Revenue by')]

  # drop na rows
  df = df.dropna()

  # if the first two columns got "stuck together"
  if df.iloc[:,0].str.contains('%').any():
    new_cols = df.columns[0].rsplit(" ", 1) # extract new first col names
    df[new_cols] = df.iloc[:,0].str.rsplit(" ", 1, expand=True) # split first column
    df = df.iloc[: , 1:] # drop first column 
  
  df = df.rename({df.columns[0]: 'Technology'}, axis=1) # rename tech col
  df = df.set_index('Technology') # set to index

  return df


def clean_tsmc_segment(df):
  """
  Cleans TSMC's segment dataframe.
  """
  # if unnamed, replace colnames with first row
  while not df.columns.str.contains('Net Revenue').any():
    df.columns = df.iloc[0]
    df = df[1:]
  
  # remove any other unnamed columns
  df = df.loc[:, df.columns.notna()]
  df = df.loc[:, df.columns.str.match(r'\dQ\d{2}') | df.columns.str.contains('Revenue by')]

  df = df.dropna()

  df = df.rename({df.columns[0]: 'Segment'}, axis=1) # rename revenue col
  df = df.set_index('Segment') # set to index
  return df

"""
Cleans TSMC's geography dataframe.
"""
def clean_tsmc_geo(df):

  # if unnamed, replace colnames with first row
  while not df.columns.str.contains('Net Revenue').any():
    df.columns = df.iloc[0]
    df = df[1:]

  # remove any other unnamed columns
  df = df.loc[:, df.columns.notna()]
  df = df.loc[:, df.columns.str.match(r'\dQ\d{2}') | df.columns.str.contains('Revenue by')]

  # drop last column
  df = df.dropna()

  # if the first two columns got "stuck together"
  if df.iloc[:,0].str.contains('%').any():
    new_cols = df.columns[0].rsplit(" ", 1) # extract new first col names
    df[new_cols] = df.iloc[:,0].str.rsplit(" ", 1, expand=True) # split first column
    df = df.iloc[: , 1:] # drop first column 
  
  df = df.rename({df.columns[0]: 'Geography'}, axis=1) # rename tech col
  df = df.set_index('Geography') # set to index

  return df

"""
Extracts capital expenditures from TSMC text pdf.
"""
def extract_tsmc_capex(pdf):
  text = [p.extract_text() for p in pdf.pages if 'V. CapEx' in p.extract_text()][0] # find page with capex
  capex_text = text.split('V. CapEx')[1] # split to part with capex
  quarters = sorted(set(re.findall('\dQ\d{2}', capex_text)), key=lambda x: x[2:] + x[:2]) # find quarters mentioned
  capex = re.findall(' (\d+\.\d{2})', capex_text)[:len(quarters)] # extract capex numbers
  return pd.DataFrame({'quarter':quarters, "capex":capex}) # return as df

"""
Extracts inventory from TSMC text pdf.
"""
def extract_tsmc_inv(pdf):
    text = [p.extract_text() for p in pdf.pages if 'Inventories' in p.extract_text()][0] # find page with capex
    quarters = re.search('(\dQ\d{2})\s*(\dQ\d{2})\s*(\dQ\d{2})', text).groups()
    inventory = re.search('Inventories\s*(\d+\.\d+)\s*(\d+\.\d+)\s*(\d+\.\d+)\s', text).groups()
    return pd.DataFrame({'quarter':quarters, "inv":inventory}) # return as df

"""
Semiconductor Manufacturing International Corporation
"""

def parse_smic_pdfplumber(url):
    dfs = read_pdf(url, pages=[5, 6, 7, 8, 9])
    df = [df for df in dfs if 'Revenue Analysis' in df.columns][0]
    
    rq = requests.get(url)
    pdf = pdfplumber.open(BytesIO(rq.content))
    inv_df = extract_smic_inv(pdf)
    capex_df = extract_smic_capex(pdf)
    
    indices = df[df.iloc[:, 0].str.contains(r"By Geography|By Service Type|By Application|By Technology")].index.tolist()
    geo_df = promote_row(df.iloc[indices[0]:indices[1], :])
    service_df = promote_row(df.iloc[indices[1]:indices[2]-1, :])
    segment_df = promote_row(df.iloc[indices[2]:indices[3], :])
    tech_df = promote_row(df.iloc[indices[3]:, :])
    
    return {'inv': inv_df, 'capex' : capex_df,'geo':geo_df, 'service' : service_df, 
    'segment' : segment_df, 'tech' : tech_df}

def promote_row(df):
  df.columns = df.iloc[0]
  df = df[1:].reset_index(drop=True)
  df.index.name = None
  return df

def extract_smic_inv(pdf):
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

def extract_smic_capex(pdf, quarter):
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
    if quarter == '12Q4':
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
        print(target_text)
        quarters = re.findall('\d[QH]\d\d', target_text)
        if not quarters:
          quarters = re.findall('\d\dQ\d', target_text)
          quarters = [q[:2] + q[2:] for q in quarters]
        quarters = [q.replace('H', 'Q') for q in quarters]
        capex = re.findall('\$([\d\.,]+) million', target_text) or re.findall('\$([\d\.,]+)M', target_text)
    return pd.DataFrame({'quarter':quarters, "capex":capex})


"""
United Microelectronics Corporations
"""

"""
Read UMC quarterly management reports and 
extract revenue by technology, revenue by platform,
revenue by geography, and capex.
"""
def pull_umc(year_quarter, url):
    data_umc = []
    try:
        umc_dfs = parse_umc(url)
        dict_geo_options_umc = {'North America':'NORAM', 'Asia Pacific':'ASIAPAC'}
                    
        umc_geo = umc_dfs.get('geo')
        for index, row in umc_geo.iterrows():
            sub_geo = row[0]
            sub_geo_value = row[1]
            if sub_geo in dict_geo_options_umc:
                sub_geo = dict_geo_options_umc.get(sub_geo)
            aggregated_geo = {'company': 'UMC', 'quarter': year_quarter, 'metric': 'rev_geo', 'sub-metric' : sub_geo, 'value': sub_geo_value}
            data_umc.append(aggregated_geo)
        umc_tech = umc_dfs.get('tech')
        for index, row in umc_tech.iterrows():
            sub_tech = row[0]
            sub_tech_value = row[1]
            aggregated_tech = {'company': 'UMC', 'quarter': year_quarter, 'metric': 'rev_tech', 'sub-metric' : sub_tech, 'value': sub_tech_value}
            data_umc.append(aggregated_tech)
    except:
        print(year_quarter, url)
    
    return data_umc

def parse_umc(url):
    rq = requests.get(url)
    pdf = pdfplumber.open(BytesIO(rq.content))
    umc_text = ""
    for i in range(10):
        umc_text += pdf.pages[i].extract_text()
    tech_df = clean_umc_tech_robust(umc_text)
    segment_df = clean_umc_seg(umc_text)
    geo_df = clean_umc_geo(umc_text)
    capex_df = "INSERT CAPEX INFO HERE"
    return {'tech': tech_df, 'segment': segment_df, 'geo': geo_df, 'capex' : capex_df}

def clean_umc_tech_robust(umc_text):
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
    digits = "\s+(\d+%)\s+(\d+%)\s+(\d+%)\s+(\d+%)\s+(\d+%)"
    quarters = "\s+(\dQ\d{2})\s+(\dQ\d{2})\s+(\dQ\d{2})\s+(\dQ\d{2})\s+(\dQ\d{2})"
    segCols = np.asarray(re.findall(f"(Customer Type){quarters}", umc_text)[0])
    Fabless = np.asarray(re.findall(f"(Fabless){digits}", umc_text)[0])
    IDM = np.asarray(re.findall(f"(IDM){digits}", umc_text)[0])
    umcSeg = np.array([Fabless, IDM])
    segDF = pd.DataFrame(umcSeg, columns=segCols)
    return segDF

def clean_umc_geo(umc_text):
    regionCols = np.asarray(re.findall(r"(Region)\s+(\dQ\d{2})\s+(\dQ\d{2})\s+(\dQ\d{2})\s+(\dQ\d{2})\s+(\dQ\d{2})", umc_text)[0])
    NorthAm = np.asarray(re.findall(r"(North America)\s+(\d+%)\s+(\d+%)\s+(\d+%)\s+(\d+%)\s+(\d+%)", umc_text)[0])
    APAC = np.asarray(re.findall(r"(Asia Pacific)\s+(\d+%)\s+(\d+%)\s+(\d+%)\s+(\d+%)\s+(\d+%)", umc_text)[0])
    Europe = np.asarray(re.findall(r"(Europe)\s+(\d+%)\s+(\d+%)\s+(\d+%)\s+(\d+%)\s+(\d+%)", umc_text)[0])
    Japan = np.asarray(re.findall(r"(Japan)\s+(\d+%)\s+(\d+%)\s+(\d+%)\s+(\d+%)\s+(\d+%)", umc_text)[0])
    umcRegions = np.array([NorthAm, APAC, Europe, Japan])
    geoDF = pd.DataFrame(umcRegions, columns=regionCols)
    return geoDF