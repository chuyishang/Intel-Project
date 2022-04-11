import pandas as pd
import numpy as np
from prophet import Prophet

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

"""
Forecasts data given df and timeframe
"""
def fut_forecast(df, year):

    m = Prophet()
    m.fit(df)
    
    future = m.make_future_dataframe(periods=len(timeframe))
    future.tail()

    forecast = m.predict(future)
    return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]

# TO DO: Process data for metrics with submetrics
# QUESTION: Plot multiple companies forecasts together?