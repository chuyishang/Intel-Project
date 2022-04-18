import pandas as pd
import numpy as np
from prophet import Prophet
import json

"""
Reformats df to have two columns, one datetime column and one value column
"""
def df_datetime_metric(json_f, metric):
    with open("data/" + json_f) as f:
        data = json.load(f)
    df = pd.DataFrame(data)
    df["combined"] = df["year"].astype(str) + "-" + df["quarter"].astype(str)
    df["ds"] = pd.to_datetime(df['combined'], errors='coerce')
    df = df.drop(["combined", "year", "quarter", "company", "sub-metric"], axis=1)
    df = df[['metric', 'ds', 'value']]
    df = df.loc[df['metric'] == metric]
    df = df.drop(["metric"], axis=1)
    df = df.rename(columns={"value": "y"})
    return df

"""
Forecasts data given df, metric, and year
"""
def fut_forecast(df, metric, years=3):
    df = df_datetime_metric(df, metric)
    m = Prophet()
    m.fit(df)

    future = m.make_future_dataframe(periods=years)

    forecast = m.predict(future)
    return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]

# TO DO: Process data for metrics with submetrics
# QUESTION: Plot multiple companies forecasts together?

# df_datetime_metric("tsmc_json_data.json", 'capex')
fut_forecast("tsmc_json_data.json", 'capex')
