"""
Imports
"""
import time
import requests
import pandas as pd
import numpy as np
import threading
import matplotlib
import sklearn
import os
import sys
import converter
import stocks

"""
Preprocessing for UMC Example
"""
UMC = stocks.get_revenue('UMC')
#UMC_customers = stocks.get_revenue_list('UMC')
QCOM = stocks.get_revenue('QCOM')
AMD = stocks.get_revenue('AMD')
conv = converter.Converter()
UMC.at[14, 'totalRevenue'] = conv.usd_twd(float(UMC.at[14, 'totalRevenue']), 2018, 2)
UMC.at[18, 'totalRevenue'] = conv.usd_twd(float(UMC.at[18, 'totalRevenue']), 2017, 2)
UMC = UMC.iloc[::-1]
QCOM = QCOM.iloc[::-1]
AMD = AMD.iloc[::-1]
UMC["revChange"] = pd.to_numeric(UMC.totalRevenue).diff()
UMC["pctRevChange"] = pd.to_numeric(UMC.totalRevenue).pct_change()
QCOM["revChange"] = pd.to_numeric(QCOM.totalRevenue).diff()
QCOM["pctRevChange"] = pd.to_numeric(QCOM.totalRevenue).pct_change()
AMD["revChange"] = pd.to_numeric(AMD.totalRevenue).diff()
AMD["pctRevChange"] = pd.to_numeric(AMD.totalRevenue).pct_change()
UMC.pctRevChange.plot()