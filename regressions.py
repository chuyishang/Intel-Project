"""
Imports
"""
import time
import requests
import pandas as pd
import numpy as np
import threading
import matplotlib
import sklearn
import os
import sys
import converter
import stocks
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import csv

print(os.getcwd())
intel_dir = os.getcwd()
data_folder_path = os.path.join(intel_dir, 'data')
print(data_folder_path)
os.chdir(data_folder_path)

dat_df = pd.read_csv('data.csv')
print(data_df)


"""
UMC Multiple Linear Regression Example
"""

"""
UMC = stocks.get_revenue('UMC')
UMC_customers = stocks.get_revenue_list(stocks.top_customers['UMC'])
conv = converter.Converter()
UMC.at[14, 'totalRevenue'] = conv.usd_twd(float(UMC.at[14, 'totalRevenue']), 2018, 2)
UMC.at[18, 'totalRevenue'] = conv.usd_twd(float(UMC.at[18, 'totalRevenue']), 2017, 2)
UMC = UMC.iloc[::-1]
UMC_customers = UMC_customers.iloc[::-1]

UMC["revChange"] = pd.to_numeric(UMC.totalRevenue).diff()
UMC["pctRevChange"] = pd.to_numeric(UMC.totalRevenue).pct_change()
UMC_customers["qcom_revChange"] = pd.to_numeric(UMC_customers.qcom_revenue).diff()
UMC_customers["qcom_pctRevChange"] = pd.to_numeric(UMC_customers.qcom_revenue).pct_change()
UMC_customers["amd_revChange"] = pd.to_numeric(UMC_customers.amd_revenue).diff()
UMC_customers["amd_pctRevChange"] = pd.to_numeric(UMC_customers.amd_revenue).pct_change()

y_umc = UMC.pctRevChange[2:].to_numpy()
x_qcom = UMC_customers.qcom_pctRevChange[1:].to_numpy().reshape(-1,1)
x_amd = UMC_customers.amd_pctRevChange[1:].to_numpy().reshape(-1,1)
x_combined = np.hstack((x_qcom, x_amd))
x_combined_df = pd.DataFrame(x_combined, columns = ['qcom','amd'])

model_linear = LinearRegression()
reg = model_linear.fit(x_combined,y_umc)
r_sq = model_linear.score(x_combined, y_umc)
predicted = reg.predict(x_combined)

#To Do: cutoff here
plt.plot(list(range(len(x_combined))), reg.predict(x_combined), label = 'Predicted UMC Rev')
plt.plot(list(range(len(x_combined))), y_umc, label = 'Actual UMC Rev')
plt.legend()
plt.show()

colors = ['Positive' if c > 0 else 'Negative' for c in model_linear.coef_]

fig = px.bar(
    x = x_combined_df.columns, y = model_linear.coef_, color=colors,
    color_discrete_sequence=['red', 'blue'],
    labels=dict(x='Feature', y='Linear coefficient'),
    title='Weight of each customer for predicting company revenue'
)
fig.show()
"""

"""
Preprocessing for linear regression
"""
def preprocess(company, customers):
    """
    Preprocessing for company revenue data from data.csv
    """

    """
    Preprocessing for customers revenue data from stocks.py
    """
    if customers == 'ALL':
        customers_df = stocks.get_revenue_list(stocks.top_customers['UMC'])
        customers_df = customers_df.iloc[::-1]
        
    
    for customer in customers:
        customer

    print(stocks.top_customers['UMC'][0])

"""
Multiple Linear Regression Function, can input specific customers or 'ALL'
"""
def regression(company, customers):
    """
    Preprocessing for company revenue data
    """
    company_df = stocks.get_revenue(company)
    if company == 'UMC':
        company_df.at[14, 'totalRevenue'] = conv.usd_twd(float(company_df.at[14, 'totalRevenue']), 2018, 2)
        company_df.at[18, 'totalRevenue'] = conv.usd_twd(float(company_df.at[18, 'totalRevenue']), 2017, 2)
    company_df = company_df.iloc[::-1]
    company_df["pctRevChange"] = pd.to_numeric(company_df.totalRevenue).pct_change()
    y_company = company_df.pctRevChange[2:].to_numpy()
    """
    Preprocessing for customers revenue data
    """
    if customers == 'ALL':
        customers_df = stocks.get_revenue_list(stocks.top_customers['UMC'])
        customers_df = customers_df.iloc[::-1]
        
    
    for customer in customers:
        customer
    
    #To Do: create x_combined variable with all customers and x_combined_df

    """
    Multiple linear regression model
    """
    model_linear = LinearRegression()
    reg = model_linear.fit(x_combined, y_company)
    r_sq = model_linear.score(x_combined, y_company)
    predicted = reg.predict(x_combined)

    plt.plot(list(range(len(x_combined))), reg.predict(x_combined), label = 'Predicted Company Rev')
    plt.plot(list(range(len(x_combined))), y_company, label = 'Actual Company Rev')
    plt.legend()
    plt.show()

    colors = ['Positive' if c > 0 else 'Negative' for c in model_linear.coef_]

    fig = px.bar(
        x = x_combined_df.columns, y = model_linear.coef_, color = colors,
        color_discrete_sequence=['red', 'blue'],
        labels = dict(x = 'Feature', y = 'Linear coefficient'),
        title = 'Weight of each customer for predicting company revenue'
    )
    fig.show()
    #To Do: return dfs of actual and predicted revenue


