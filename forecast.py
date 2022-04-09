import pandas as pd
import numpy as np
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

with open('data/tsmc_json_data.json') as f:
   data = json.load(f)
tsmc_df = pd.DataFrame(data)
# df = pd.read_json('data/tsmc_json_data.json', lines=False)
for i in np.arange(len(tsmc_df)):
    if int(tsmc_df["year"][i]) >= 0 and int(tsmc_df["year"][i]) <= 21:
        tsmc_df["year"][i] = "20" + tsmc_df["year"][i]
    else:
        tsmc_df["year"][i] = "19" + tsmc_df["year"][i]
for i in np.arange(len(tsmc_df)):
    tsmc_df["quarter"][i] = tsmc_df["quarter"][i][::-1]
tsmc_df["combined"] = tsmc_df["year"].astype(str) + "-" + tsmc_df["quarter"].astype(str)
tsmc_df["ds"] = pd.to_datetime(tsmc_df['combined'], errors='coerce')
tsmc_df = tsmc_df.drop(["combined", "year", "quarter", "company", "sub-metric"], axis=1)
tsmc_df = tsmc_df[['metric', 'ds', 'value']]
tsmc_df = tsmc_df.loc[tsmc_df['metric'] == 'capex']
tsmc_df = tsmc_df.drop(["metric"], axis=1)
tsmc_df = tsmc_df.rename(columns={"value": "y"})
# print(tsmc_df)

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


    future = m.make_future_dataframe(periods=len(timeframe))
    future.tail()

    forecast = m.predict(future)
    # forecast[['date', 'yhat', 'yhat_lower', 'yhat_upper']].tail()
    return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]

    # fig1 = m.plot(forecast)
    # fig2 = m.plot_components(forecast)

print(fut_forecast(tsmc_df, [2003,2004,2005]))
