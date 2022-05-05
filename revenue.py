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


def smic_scrape_revenue(year, quarter, url):
  rq = requests.get(url)
  pdf = pdfplumber.open(BytesIO(rq.content))
  text = ""
  text += pdf.pages[0].extract_text()
  revenue_regex = "\$\d+,*\d*\.*\d*"
  revenue = re.findall(f"{revenue_regex}", text)[0]
  revenue_no_dollar_sign = revenue.replace("$","")
  revenue_no_comma = revenue_no_dollar_sign.replace(",","")
  revenue_num = float(revenue_no_comma)
  return revenue_num


def tsmc_scrape_revenue(year, quarter, url):
  rq = requests.get(url)
  pdf = pdfplumber.open(BytesIO(rq.content))
  text = ""
  text += pdf.pages[0].extract_text()
  revenue_regex = "\$\d+,*\d*\.*\d*"
  revenue = re.findall(f"{revenue_regex}", text)[0]
  revenue_no_dollar_sign = revenue.replace("$","")
  revenue_no_comma = revenue_no_dollar_sign.replace(",","")
  revenue_num = float(revenue_no_comma)
  return revenue_num

def gf_scrape_revenue(year, quarter, url):
  rq = requests.get(url)
  pdf = pdfplumber.open(BytesIO(rq.content))
  text = ""
  text += pdf.pages[0].extract_text()
  revenue_regex = "\$\d+,*\d*\.*\d*"
  revenue = re.findall(f"{revenue_regex}", text)[0]
  revenue_no_dollar_sign = revenue.replace("$","")
  revenue_no_comma = revenue_no_dollar_sign.replace(",","")
  revenue_num = float(revenue_no_comma)
  return revenue_num

def umc_scrape_revenue(year, quarter, url):
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
  return revenue_num

#x = umc_scrape_revenue(2021, 4, 'https://www.umc.com/upload/media/08_Investors/Financials/Quarterly_Results/Quarterly_2020-2029_English_pdf/2021/Q4_2021/UMC21Q4_report.pdf')
#print(x)