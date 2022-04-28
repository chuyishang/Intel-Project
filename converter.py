import pandas as pd
import twder
import datetime
from datetime import date
from forex_python.converter import CurrencyRates

class Converter:
    def __init__(self, path='data/usd_twd.csv'):
        """
        Specify path to currency dataframe.
        """
        self.path = path
        self.twd_usd_df = pd.read_csv("data/usd_twd.csv")

    def twd_usd(self, twd_value, year, quarter):
        """
        Retrieves equivalent USD value from given year and quarter.
        """
        q_key = {1: "Jan ", 2: "Apr ", 3:"Jul ", 4:"Oct "}
        q_month = {1: 1, 2: 4, 3: 7, 4: 10}
        key = q_key[quarter] + str(year)[-2:]
        try:
            twd_usd_rate = self.twd_usd_df[self.twd_usd_df["Date"] == key]["Price"].to_numpy()[0]
        except:
            if date.today().year - 1 == year or date.today().year == year:
                try:
                    twder_ret = twder.specify_month("USD", year, q_month[quarter])
                    twd_usd_rate = (float(twder_ret[0][4]) + float(twder_ret[0][3])) / 2 #averaging buy/sell of spot market
                    self.twd_usd_df = self.twd_usd_df.append({"Date": key, "Price": twd_usd_rate}, ignore_index = True)
                    self.twd_usd_df.to_csv(self.path, index=False, index_label = "Date")
                except:
                    return
            else:
                return
        return twd_value / twd_usd_rate

    def usd_twd(self, usd_value, year, quarter):
        """
        Retrieves equivalent TWD value from given year and quarter.
        """
        q_key = {1: "Jan ", 2: "Apr ", 3:"Jul ", 4:"Oct "}
        q_month = {1: 1, 2: 4, 3: 7, 4: 10}
        key = q_key[quarter] + str(year)[-2:]
        try:
            twd_usd_rate = self.twd_usd_df[self.twd_usd_df["Date"] == key]["Price"].to_numpy()[0]
        except:
            if date.today().year - 1 == year or date.today().year == year:
                try:
                    twder_ret = twder.specify_month("USD", year, q_month[quarter])
                    twd_usd_rate = (float(twder_ret[0][4]) + float(twder_ret[0][3])) / 2 #averaging buy/sell of spot market
                    self.twd_usd_df = self.twd_usd_df.append({"Date": key, "Price": twd_usd_rate}, ignore_index = True)
                    self.twd_usd_df.to_csv(self.path, index=False, index_label = "Date")
                except:
                    return
            else:
                return
        return usd_value * twd_usd_rate

    def jpy_usd(self, jpy_value, year, quarter):
        c = CurrencyRates()
        year_quarter = str(year) + "-" + "Q" + str(quarter)
        datetime_obj = pd.to_datetime(year_quarter)
        conversion_rate = c.get_rate('USD', 'JPY', datetime_obj)
        return jpy_value / conversion_rate