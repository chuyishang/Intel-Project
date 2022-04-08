import pandas as pd
from prophet import Prophet

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


def fut_forecast(df, timeframe):
    m = Prophet()
    m.fit(df)
    # need to convert year and quarter to single datetime field, name column "date"

    future = m.make_future_dataframe(freq="year",periods=len(timeframe))
    future.tail()

    forecast = m.predict(future)
    forecast[['date', 'yhat', 'yhat_lower', 'yhat_upper']].tail()
