from codecs import ignore_errors
import time
import requests
import pandas as pd
import numpy as np
import threading
import converter
import time
from forex_python.converter import CurrencyRates

api_key = '2CCS30TFYFGYBXKB'
# Dictionary mapping each competitor's ticker to a list of its top customers' ticker, if the customer is on a US stock exchange
top_customers = {'TSMC':['AAPL', 'AMD', 'QCOM', 'AVGO', 'NVDA', 'SONY', 'MRVL', 'STM', 'ADI', 'INTC'],
                'SMIC':['QCOM', 'AVGO', 'TXN'],
                'UMC':['QCOM', 'AMD'],
                'GFS':['QCOM', 'NXPI', 'QRVO', 'CRUS', 'AMD', 'SWKS', 'AVGO']
            }
# Tracks number of calls to API so the program can sleep once it reaches 5
call_count = 0
start_time = time.time()
'''
Returns DataFrame with past 5 years of quarterly revenue for TICKER. If data does not exist, return empty DataFrame.
DataFrame columns: ['reportedCurrency', 'totalRevenue', 'year', 'quarter']
'''
def get_revenue(ticker):
    global call_count, start_time
    if call_count >= 5:
        time.sleep(max(60 - (time.time() - start_time), 0))
        call_count = 0
        start_time = time.time()
    url = f'https://www.alphavantage.co/query?function=INCOME_STATEMENT&symbol={ticker}&apikey={api_key}'
    call_count += 1
    r = requests.get(url)
    json_data = r.json()
    if json_data:
        quarter_data = pd.DataFrame.from_dict(json_data['quarterlyReports'])
        revenue_df = quarter_data[["fiscalDateEnding", "reportedCurrency", "totalRevenue"]]
        revenue_df.insert(0, 'quarter', [int(s.split("-")[1]) // 3 for s in revenue_df["fiscalDateEnding"]])
        revenue_df.insert(0, 'year', [int(s.split("-")[0]) for s in revenue_df["fiscalDateEnding"]])
        revenue_df.drop(["fiscalDateEnding"], axis=1, inplace=True)
        if min(revenue_df['quarter']) == 0:
            revenue_df['quarter'] = [q + 1 for q in revenue_df['quarter']]
        revenue_df['totalRevenue'] = pd.to_numeric(revenue_df['totalRevenue'], errors='ignore')
        if revenue_df["reportedCurrency"][0] == "TWD":
            revenue_df["reportedCurrency"] = revenue_df["reportedCurrency"].map(lambda x:"USD", na_action='ignore')
            revenue_df["totalRevenue"] = revenue_df.apply(lambda x:converter.Converter().twd_usd(x[-1], x[0], x[1]) if x[-1] else None, axis=1)
        revenue_df.rename({"totalRevenue":f'{ticker.lower()}_revenue'}, axis=1, inplace=True)
        return revenue_df
    return pd.DataFrame()

'''
Returns DataFrame with past 5 years of quarterly revenue for all companies in tickerList.
'''
def get_revenue_list(ticker_list=[]):
    df = pd.DataFrame()
    for ticker in ticker_list:
        ticker_df = get_revenue(ticker)
        if ticker_df["reportedCurrency"][0] == "TWD":
            ticker_df["reportedCurrency"] = ticker_df["reportedCurrency"].map(lambda x:"USD", na_action='ignore')
            ticker_df["totalRevenue"] = ticker_df.apply(lambda x:converter.Converter().twd_usd(x[-1], x[0], x[1]) if x[-1] else None, axis=1)
        if ticker_df["reportedCurrency"][0] == "JPY":
            ticker_df["reportedCurrency"] = ticker_df["reportedCurrency"].map(lambda x:"USD", na_action='ignore')
            ticker_df["totalRevenue"] = ticker_df.apply(lambda x:converter.Converter().jpy_usd(x[-1], x[0], x[1]) if x[-1] else None, axis=1)
        ticker_df.rename({"totalRevenue":f'{ticker.lower()}_revenue'}, axis=1, inplace=True)
        if df.empty:
            df = ticker_df
        else:
            df = pd.merge(df, ticker_df, how='outer', on=['year', 'quarter', 'reportedCurrency']).fillna(0)
    return df

'''
Returns realtime exchange rate from FROMCURR to TOCURR.
'''
def get_exchange_rate(fromCurr, toCurr):
    url = f'https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency={fromCurr}&to_currency={toCurr}&apikey={api_key}'
    r = requests.get(url)
    data = r.json()
    return data['Realtime Currency Exchange Rate']['Exchange Rate']

#print(get_revenue_list(['GFS','UMC'])) # Need to pull TSMC and SMIC revenue
#print(get_customer_revenue('TSMC'))