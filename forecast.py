import pandas as pd
import numpy as np
from prophet import Prophet
import json

"""
Converts json for specific company to df
"""
def json_to_df(json_path):
    with open(json_path) as f:
        data = json.load(f)
    df = pd.DataFrame(data)
    return df

"""
Reformats df to have two columns, one datetime column and one value column
"""
def df_datetime_metric(df, metric):
    for i in np.arange(len(df)):
        if int(df["year"][i]) >= 0 and int(df["year"][i]) <= 21:
            df["year"][i] = "20" + df["year"][i]
        else:
            df["year"][i] = "19" + df["year"][i]
    for i in np.arange(len(df)):
        df["quarter"][i] = df["quarter"][i][::-1]
    df["combined"] = df["year"].astype(str) + "-" + df["quarter"].astype(str)
    df["ds"] = pd.to_datetime(df['combined'], errors='coerce')
    df = df.drop(["combined", "year", "quarter", "company", "sub-metric"], axis=1)
    df = df[['metric', 'ds', 'value']]
    df = df.loc[df['metric'] == metric]
    df = df.drop(["metric"], axis=1)
    df = df.rename(columns={"value": "y"})
    return df

tsmc_df = json_to_df('data/tsmc_json_data.json')
tsmc_capex_df = df_datetime_metric(tsmc_df, 'capex')
print(tsmc_capex_df)

"""
Forecasts data given df and timeframe
"""
def fut_forecast(df, timeframe):

    m = Prophet()
    m.fit(df)
    
    future = m.make_future_dataframe(periods=len(timeframe))
    future.tail()

    forecast = m.predict(future)
    # forecast[['date', 'yhat', 'yhat_lower', 'yhat_upper']].tail()
    return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]

    # fig1 = m.plot(forecast)
    # fig2 = m.plot_components(forecast)

print(fut_forecast(tsmc_capex_df, [2003,2004,2005]))

# TO DO: Process data for metrics with submetrics
# QUESTION: Plot multiple companies forecasts together?