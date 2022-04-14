import time
import requests
import pandas as pd
import numpy as np
import threading

api_key = '2CCS30TFYFGYBXKB'
# Dictionary mapping each competitor's ticker to a list of its top customers' ticker, if the customer is in the US
top_customers = {'TSMC':['AAPL', 'AMD', 'QCOM', 'AVGO', 'NVDA', 'SONY', 'MRVL', 'STM', 'ADI', 'INTC'],
                'SMIC':['QCOM', 'AVGO', 'TXN'],
                'UMC':['QCOM', 'AMD'],
                'GF':['QCOM', 'NXPI', 'QRVO', 'CRUS', 'AMD', 'SWKS', 'AVGO']
            }
# Tracks number of calls to API so the program can sleep once it reaches 5
call_count = 0
'''
Returns DataFrame with past 5 years of quarterly revenue for TICKER. If data does not exist, return empty DataFrame.
DataFrame columns: ['reportedCurrency', 'totalRevenue', 'year', 'quarter']
'''
def get_revenue(ticker):
    global call_count
    if call_count == 5:
        time.sleep(60)
        call_count = 0
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
        revenue_df['totalRevenue'] = pd.to_numeric(revenue_df['totalRevenue'])
        return revenue_df
    return pd.DataFrame()

'''
Returns DataFrame with past 5 years of quarterly revenue for all companies in top_customers[COMPANY].
'''
def get_customer_revenue(company):
    df = pd.DataFrame()
    for ticker in top_customers[company]:
        ticker_df = get_revenue(ticker)
        ticker_df.rename({"totalRevenue":f'{ticker.lower()}Revenue'}, axis=1, inplace=True)
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

print(get_revenue('UMC')) # Need to pull TSMC and SMIC revenue
#rint(get_customer_revenue('TSMC'))