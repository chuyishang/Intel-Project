from codecs import ignore_errors
import json
import time
import requests
import pandas as pd
import numpy as np
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
DataFrame columns: ['year', 'quarter', 'reportedCurrency', 'revenue', 'company']
'''
def get_revenue(ticker):
    #Sleeps program after every 5 calls due to call limit
    global call_count, start_time
    if call_count >= 5:
        time.sleep(60)
        call_count = 0
        start_time = time.time()
    
    #Pulls data from API
    url = f'https://www.alphavantage.co/query?function=INCOME_STATEMENT&symbol={ticker}&apikey={api_key}'
    call_count += 1
    r = requests.get(url)
    json_data = r.json()
    if json_data:
        quarter_data = pd.DataFrame.from_dict(json_data['quarterlyReports'])
        revenue_df = quarter_data[["fiscalDateEnding", "reportedCurrency", "totalRevenue"]]

        #Converts fiscalDateEnding into quarter and year
        revenue_df.insert(0, 'quarter', [int(s.split("-")[1]) // 3 for s in revenue_df["fiscalDateEnding"]])
        revenue_df.insert(0, 'year', [int(s.split("-")[0]) for s in revenue_df["fiscalDateEnding"]])
        revenue_df.drop(["fiscalDateEnding"], axis=1, inplace=True)
        if min(revenue_df['quarter']) == 0:
            revenue_df['quarter'] = [q + 1 for q in revenue_df['quarter']]

        #Filters out non-numeric revenue values
        revenue_df['totalRevenue'] = pd.to_numeric(revenue_df['totalRevenue'], errors='ignore')
        revenue_df = revenue_df[pd.to_numeric(revenue_df['totalRevenue'], errors='coerce').notnull()]

        #Currency Conversion
        currency = revenue_df["reportedCurrency"].tolist()[0]
        if currency == "TWD":
            revenue_df["reportedCurrency"] = "USD"
            revenue_df["totalRevenue"] = revenue_df.apply(lambda x:converter.Converter().twd_usd(x[-1], x[0], x[1]) if x[-1] else None, axis=1)
        if currency == "JPY":
            revenue_df["reportedCurrency"] = "JPY"
            revenue_df["totalRevenue"] = revenue_df.apply(lambda x:converter.Converter().jpy_usd(x[-1], x[0], x[1]) if x[-1] else None, axis=1)
        
        #Processing dataframe
        revenue_df.rename({"totalRevenue":"revenue"}, axis=1, inplace=True)
        revenue_df["company"] = ticker
        print(revenue_df)
        return revenue_df
    return pd.DataFrame()

'''
Returns DataFrame with past 5 years of quarterly revenue for all companies in tickerList.
'''
def get_revenue_list(ticker_list=[]):
    df = pd.DataFrame()
    for ticker in ticker_list:
        ticker_df = get_revenue(ticker)
        df = ticker_df if df.empty else pd.concat([df, ticker_df], axis=0)
    return df

'''
Not used. Returns realtime exchange rate from FROMCURR to TOCURR.
'''
def get_exchange_rate(fromCurr, toCurr):
    url = f'https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency={fromCurr}&to_currency={toCurr}&apikey={api_key}'
    r = requests.get(url)
    data = r.json()
    return data['Realtime Currency Exchange Rate']['Exchange Rate']

#Test statements
#print(get_revenue_list(["UMC","GFS"]))
#print(get_revenue_list(top_customers['TSMC']))
#print(get_revenue('AAPL'))
