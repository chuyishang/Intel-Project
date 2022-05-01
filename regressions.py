"""
Imports
"""
from re import X
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
from parameters import DATA_FILE
import stocks
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import csv
from parameters import *

"""
Preprocessing for linear regression
"""
def preprocess(start_year, start_quarter, end_year, end_quarter, metric, company, customers):
    """
    Preprocessing for company revenue data from data.csv
    """
    intel_dir = os.getcwd()
    data_folder_path = os.path.join(intel_dir, 'data')
    #change filepath to data folder to get data.csv
    os.chdir(data_folder_path)
    data_df = pd.read_csv(DATA_FILE)
    #change filepath back to main folder
    os.chdir("..")

    #get company data on metric from data_df
    company_df = data_df[data_df["company"] == company]
    company_df = company_df[company_df["sub-metric"] == metric]
    #drop rows based on start_year and end_year
    company_df = company_df[company_df["year"] <= end_year]
    company_df = company_df[company_df["year"] >= start_year]
    company_df = company_df.drop(columns=['company', 'metric', 'sub-metric'])
    #drop rows based on start_quarter
    for index, row in company_df.iterrows():
        if row['year'] == start_year:
            if row['quarter'] < start_quarter:
                company_df.drop(index, inplace=True)
        else:
            break
    #drop rows based on end_quarter
    company_df = company_df.iloc[::-1]
    for index, row in company_df.iterrows():
        if row['year'] == end_year:
            if row['quarter'] > end_quarter:
                company_df.drop(index, inplace=True)
        else:
            break
    company_df = company_df.iloc[::-1]

    """
    Preprocessing for customers revenue data from stocks.py
    """
    if customers == 'ALL':
        customers_df = stocks.get_revenue_list(stocks.top_customers[company])
        
    else:
        customers_df = stocks.get_revenue(customers[0])
        customers_df.rename(columns={'revenue': 'placeholder'}, inplace=True)
        #customers_df.rename(columns={customers[0].lower() + '_revenue': 'placeholder'}, inplace=True)
        customers_df = customers_df.drop(columns=['reportedCurrency'])
        for indiv_customer in customers:
            indiv_customer_df = stocks.get_revenue(indiv_customer)
            indiv_customer_df = indiv_customer_df[['revenue']]
            #indiv_customer_df = indiv_customer_df[[indiv_customer.lower() + '_revenue']]
            indiv_customer_df.rename(columns={'revenue': indiv_customer.lower() + '_revenue'}, inplace=True)
            customers_df = pd.concat([customers_df, indiv_customer_df], axis=1)
        customers_df = customers_df.drop(columns=['placeholder', 'company'])

    """
    Merge company and customers df, check for 0s
    """
    merged_df = pd.merge(company_df, customers_df, how='inner', left_on=['year', 'quarter'], right_on =['year', 'quarter'])
    #check if there are zeros in any customer rev, if so, throw error
    merged_df_columns = list(merged_df.columns.values.tolist())
    customer_names_list = merged_df_columns[3:]
    for indiv_customer in customer_names_list:
        customer_values = merged_df[indiv_customer].tolist()
        if 0 in customer_values:
            print("Error: revenue value of 0 for customer " + indiv_customer)
            quit()

    """
    Extract pctRevChange for company into numpy array
    """
    merged_df["pctRevChange"] = pd.to_numeric(merged_df.value).pct_change()
    y_company = merged_df.pctRevChange[1:].to_numpy()
    
    """
    Extract pctRevChange for customers into numpy array
    """
    merged_df["placeholder"] = pd.to_numeric(merged_df.iloc[:, 3]).pct_change()
    x_customers = merged_df.placeholder[1:].to_numpy().reshape(-1,1)
    for indiv_customer in customer_names_list:
        merged_df["customer_pctRevChange"] = pd.to_numeric(merged_df[indiv_customer]).pct_change()
        x_indiv_customer = merged_df.customer_pctRevChange[1:].to_numpy().reshape(-1,1)
        x_customers = np.hstack((x_customers, x_indiv_customer))
        merged_df.drop(columns=['customer_pctRevChange'])
    x_customers = np.delete(x_customers, 0, axis=1)

    results_array = [y_company, x_customers]
    return results_array


"""
Multiple Linear Regression Function, can input specific customers or 'ALL'
"""
def regression(y_company, x_customers, company, customers, startYear, startQuarter, endYear, endQuarter):
    """
    Multiple linear regression model
    """
    model_linear = LinearRegression()
    reg = model_linear.fit(x_customers, y_company)
    r_sq = model_linear.score(x_customers, y_company)
    predicted = reg.predict(x_customers)
    coefficients = model_linear.coef_

    #Predicted vs. actual line graph
    quarter_strings = [f"{(startQuarter + i - 1) % 4 + 1}Q{(startYear + i // 4) % 100}" for i in range(len(x_customers))]
    predicted_df = pd.DataFrame({"Quarter":quarter_strings, "Percent Change":reg.predict(x_customers), "Type":"Predicted"})
    actual_df = pd.DataFrame({"Quarter":quarter_strings, "Percent Change":y_company, "Type":"Actual"})
    prediction_df = pd.concat([predicted_df, actual_df], axis=0)
    prediction_fig = px.line(prediction_df, "Quarter", "Percent Change", color="Type", title = f"Quarterly Change in Revenue for {company}")

    #Linear coefficient bar graph
    colors = ['Positive' if c > 0 else 'Negative' for c in model_linear.coef_]
    x_combined_df = pd.DataFrame(x_customers, columns = customers)
    coeff_fig = px.bar(
        x = x_combined_df.columns, y = model_linear.coef_, color = colors,
        color_discrete_map={'Positive':'green', 'Negative':'red'},
        labels = dict(x = 'Feature', y = 'Linear Coefficient', color = "Sign"),
        title = f'Visualizing coefficients for multiple linear regression (MLR) for {company}'
    )

    return r_sq, predicted, coefficients, model_linear, reg, prediction_fig, coeff_fig

    
#x = preprocess(2015, 3, 2020, 1, 'NORAM', 'TSMC', ['AAPL', 'QCOM'])
#y = regression(x[0], x[1], 'TSMC', ['AAPL', 'QCOM'])
#print(y)