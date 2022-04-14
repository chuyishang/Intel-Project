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


x = tsmc_scrape_revenue(2013, 4, 'https://investor.tsmc.com/english/encrypt/files/encrypt_file/english/2013/Q4/4Q13ManagementReport.pdf')
print(x)