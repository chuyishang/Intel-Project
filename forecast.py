import pandas as pd
from prophet import Prophet
import json

"""

df = pd.read_csv('../examples/example_wp_log_peyton_manning.csv')
df.head()

m = Prophet()
m.fit(df)

future = m.make_future_dataframe(periods=365)
future.tail()

forecast = m.predict(future)
forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail()

fig1 = m.plot(forecast)

fig2 = m.plot_components(forecast)

"""

"""
Processes data for TSMC Capex, turns json into dataframe
"""
df = pd.read_json('data/tsmc_json_data.json')
df["date"] = df["year"].astype(str) + df["quarter"]
df = df.drop(["year", "quarter", "company", "sub-metric"], axis=1)
df = df[['metric', 'date', 'value']]
df = df.loc[df['metric'] == 'capex']
df = df.drop(["metric"], axis=1)
"""
Returns df with one column with year + quarter and one column as value
"""


"""
Forecasts data given df and timeframe
"""
def fut_forecast(df, timeframe):
    
    m = Prophet()
    m.fit(df)
    # need to convert year and quarter to single datetime field, name column "date"


    future = m.make_future_dataframe(freq="year",periods=len(timeframe))
    future.tail()

    forecast = m.predict(future)
    forecast[['date', 'yhat', 'yhat_lower', 'yhat_upper']].tail()

    fig1 = m.plot(forecast)
    fig2 = m.plot_components(forecast)
