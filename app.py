from cmath import nan
from logging import Filterer
from threading import local
#Dash imports
from dash import Dash, html, dcc, Input, Output, State, callback_context, dash_table
import dash_bootstrap_components as dbc
import dash_daq as daq
import plotly.express as px
import plotly.graph_objs as go
#Forecasting imports
from prophet import Prophet
from forecast import *
from prophet.plot import plot_plotly, plot_components_plotly
#Import other files in directory
import scraper, stocks, pickle, regressions, converter
from parameters import *
#Data analysis imports
import pandas as pd
import numpy as np
from datetime import datetime
import re

pd.options.mode.chained_assignment = None
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

#Styling for help buttons
roundbutton = {
    "backgroundColor": "#15B8FC",
    "border": "2px solid #15B8FC",
    "border-radius": "50%",
    "padding": 0,
    "color": "white",
    "textAlign": "center",
    "display": "inline",
    "fontSize": 15,
    "height": 30,
    "width": 30,
}

#Read DATA_FILE to populate global dataset
global_df = pd.read_csv(DATA_FILE)
global_df = global_df.drop_duplicates()
global_df['value'] = global_df['value'].astype(str).str.replace(",","").astype(float)
global_df['year'] = global_df['year'].astype(int)
global_df['quarter'] = global_df['quarter'].astype(int)

#Read REVENUE_FILE, sets to empty df if csv is empty
try:
    revenue_df = pd.read_csv(REVENUE_FILE)
except:
    revenue_df = pd.DataFrame()

#Global dictionaries and variables
metric_to_var = {"Revenue by Technology": "rev_tech", "Revenue by Segment": "rev_seg", "Revenue by Geography": "rev_geo", "CapEx": "capex", "Inventory": "inv", "Revenue":"rev", "Gross Margin":"gross_margin"}
var_to_metric = {v:k for k, v in metric_to_var.items()}
company_abbrev = {"SMIC": "smic", "UMC": "umc", "Global Foundries": "gf", "TSMC":"tsmc"}
firstYear = 2000
currYear = datetime.now().year

#Get regression predictor options
predictor_options = revenue_df["company"].unique() if not revenue_df.empty else []

#Read ticker options
with open(TICKER_FILE, "rb") as f:
    ticker_options = pickle.load(f)

#Visualization tab input panel
controls = dbc.Card(
    [  
        html.Div(
            [
                dbc.Label("Company"),
                dcc.Dropdown(
                    id="company-dropdown",
                    options=[
                       "TSMC", "SMIC", "UMC", "Global Foundries"
                    ],
                ),
            ]
        ),
        html.Div(
            [
                dbc.Label("Metric"),
                dcc.Dropdown(
                    id="metric-dropdown",
                    options = ["Revenue by Technology", "Revenue by Segment", "Revenue by Geography", "CapEx", "Inventory"],
                ),
            ]
        ),

        html.Div(
            [
                dbc.Label("Visualization Style"),
                dcc.Dropdown(
                    id="viz-dropdown",
                ),
            ]
        ),

        html.Div(
            [
                dbc.Label("Submetric"),
                dcc.Dropdown(
                    id="submetric-dropdown",
                    value=""
                ),
                
            ]
        ),

        html.Div(
            [
                dbc.Label("Starting Year", html_for="start-dropdown"),
                dcc.Dropdown(
                    options= np.arange(firstYear, currYear),
                    id = "start-dropdown"
                ),
                dbc.Label("Starting Quarter", html_for="startq-dropdown"),
                dcc.Dropdown(
                    options= ["1", "2", "3", "4"],
                    id = "startq-dropdown"
                )
            ],
            className="mb-3", style={'width': '48%', 'float': 'left', 'display': 'inline-block', 'margin': '10'}
        ),

        html.Div(
            [
                dbc.Label("Ending Year", html_for="end-dropdown"),
                dcc.Dropdown(
                    options= np.arange(firstYear, currYear),
                    id = "end-dropdown"
                ),
                dbc.Label("Ending Quarter", html_for="endq-dropdown"),
                dcc.Dropdown(
                    options = ["1", "2", "3", "4"],
                    id = "endq-dropdown"
                )
                
            ],
            className="mb-3", style={'width': '48%', 'float': 'left', 'margin': '10', 'display':'inline-block'}
        ),
        html.Div([
            dbc.Label("Turn on Forecast", html_for="forecasting_switch"),
            daq.BooleanSwitch(id='forecasting-switch', on=False),
            dbc.Label("Years to Forecast", html_for="forecasting-dropdown"),
            dcc.Dropdown(
                options = ["1", "2", "3", "4","5","6","7","8"],
                id = "forecasting-dropdown",
                value="3",
                style={"margin-bottom": 10})
        ],
        ),
        html.Div([
            dbc.Button("Download Data", className="ms-auto", id= "btn-data"),
            dcc.Download(id="download-data-csv"),
            dcc.Store(id="dataframe", data=[]),
            dcc.Store(id="json-store", data=[])
        ])
        
    ],
    body=True,
)

#Scraping tab input panel
parsing = html.Div(
    [
    dbc.Card(
    [
        html.H3("PDF Scraper"),
        html.Div(
            [
                dbc.Label("URL"),
                dbc.Input(
                    id="url-input".format("url"),
                    type="url",
                    placeholder="Enter URL to Parse".format("url"),
                ),
            ],
        ),
        html.Div(
            [
                dbc.Label("Company"),
                dcc.Dropdown(
                    id="company-input",
                    options=[
                       "TSMC", "SMIC", "UMC", "Global Foundries"
                    ],
                ),
            ],
        ),
        html.Div(
            [
                dbc.Label("Year"),
                dbc.Input(
                    id="year-input".format("number"),
                    type="number",
                    placeholder="Enter Year".format("number"),
                ),
            ],
        ),
        html.Div(
            [
                dbc.Label("Quarter"),
                dcc.Dropdown(
                    id="quarter-input",
                    options=[1, 2, 3, 4]
                ),
            ],
        ),
        html.Div(
            [
                dbc.Button("Scrape PDF", id= "btn-scrape", style={"margin-top": 10}, className="ms-auto", n_clicks=0),   
            ]
        ),
    ],
    body=True,
    style={"margin-bottom": 10}
    ),
    dbc.Card(
    [
        html.H3("Manual Input"),
        html.Div(
            [
                dbc.Label("Company"),
                dcc.Dropdown(
                    id="manual-company-input",
                    options=[
                       "TSMC", "SMIC", "UMC", "Global Foundries"
                    ],
                ),
            ],
        ),
        html.Div(
            [
                dbc.Label("Year"),
                dbc.Input(
                    id="manual-year-input".format("number"),
                    type="number",
                    placeholder="Enter Year".format("number"),
                ),
            ],
        ),
        html.Div(
            [
                dbc.Label("Quarter"),
                dcc.Dropdown(
                    id="manual-quarter-input",
                    options=[1, 2, 3, 4]
                ),
            ],
        ),
        html.Div(
            [
                dbc.Button("Start Manual Input", id= "btn-manual", style={"margin-top": 10}, className="ms-auto", n_clicks=0),   
            ]
        )
    ],
    body=True,
    )
    ]
)

#Pulling tab input panel
puller = dbc.Card(
    [
        html.Div([
            dbc.Label("Custom Ticker"),
            dbc.Input(
                    id="input-ticker",
                    value=""
                ),
        ],
        ),

        html.Div(
            dbc.ButtonGroup([
            dbc.Button("Add Ticker", id= "btn-add-ticker", style={"margin-top": 10, "margin-bottom": 10}, outline=True, color="primary", n_clicks=0),
            dbc.Button("Remove Ticker", id= "btn-remove-ticker", style={"margin-top": 10, "margin-bottom": 10}, outline=True, color="primary", n_clicks=0),])
        ),
        html.Div([
            dbc.Label("Company Tickers"),
            dcc.Dropdown(
                    id="ticker-dropdown",
                    options=ticker_options,
                    multi=True
                ),
            ]
        ),
        html.Div(
            [dbc.ButtonGroup([
                dbc.Button("Update Selected Tickers", id="btn-pull", style={"margin-top": 10}, outline=True, color="primary", n_clicks=0),
                dbc.Button("Update All Tickers", id="btn-update-all", style={"margin-top": 10}, outline=True, color="primary", n_clicks=0),   
            ]),
            ]
        ),
        html.Div(
            [
                dcc.Download(id="download-rev-csv"),
                #dcc.Store(id="json-store-pull", data=[])
                
            ]
        ),

    ],
    body=True
)

#Scraper tab: Automatic scraper action buttons
buttons = html.Div(
    [
        html.Div(
            [dbc.ButtonGroup([
            dbc.Button("Approve", id= "btn-approve", style={"margin-right": 10, "display":"none"}, color="primary", outline=True, n_clicks=0),   
            dbc.Button("Reject", id= "btn-reject", style={"margin-right": 10, "display":"none"}, color="primary", outline=True, n_clicks=0),
            dbc.Button("Undo", id= "btn-undo",  style={"margin-right": 10, "display":"none"}, color="primary", outline=True, n_clicks=0)],
            )
            ]   
        ),
        html.Div(
            id='confirmation-msg',
            children='Press "Approve" to confirm that the scraped data is accurate.',
            style={"display":"none"}
        ),    
    ],
    id = "auto-parsing-buttons",
    style={"display":"inline"},
)

#Scraper tab: Manual input action buttons
manual_buttons = html.Div(
    [
        html.Div(
            [
            dbc.ButtonGroup([
            dbc.Button("Add to Data", id= "btn-add", style={"margin-right": 10, "display":"none"}, color="primary", outline=True, n_clicks=0),   
            dbc.Button("Undo", id= "btn-undo-manual", style={"margin-right": 10, "display":"none"}, color="primary", outline=True, n_clicks=0)])
            ],
            style={"margin-top":10}   
        ),
        html.Div(
            id='confirmation-msg2',
            children='Press "Add to Data" to add the manually inputted data to the dataset.',
            style={"display":"none"}
        ),    
    ],
)

#Regression tab input panel
regression = dbc.Card(
    [
        html.Div(
            [
                dbc.Label("Competitor"),
                dcc.Dropdown(
                    id="regression-comp-dropdown",
                    options=[
                       "TSMC", "SMIC", "UMC", "Global Foundries"
                    ],
                    style={"margin-bottom": 10}
                ),
            ],
        ),

        html.Div([
            dbc.Label("Revenue Segment"),
            dcc.Dropdown(
                    id="regression-segment-dropdown",
                    options=[],
                ),
            ]
        ),
        
        html.Div([
            dbc.Label("Predictor Company"),
            dcc.Dropdown(
                    id="regression-ticker-dropdown",
                    options=predictor_options,
                    multi=True
                ),
            ]
        ),

        html.Div(
            [
                dbc.Label("Starting Year"),
                dcc.Dropdown(
                    options = np.arange(firstYear, currYear),
                    id = "regression-start-dropdown"
                ),
                dbc.Label("Starting Quarter"),
                dcc.Dropdown(
                    options= ["1", "2", "3", "4"],
                    id = "regression-startq-dropdown"
                )
            ],
            className="mb-3", style={'width': '48%', 'float': 'left', 'display': 'inline-block', 'margin': '10'}
        ),

        html.Div(
            [
                dbc.Label("Ending Year"),
                dcc.Dropdown(
                    options= np.arange(firstYear, currYear),
                    id = "regression-end-dropdown"
                ),
                dbc.Label("Ending Quarter"),
                dcc.Dropdown(
                    options = ["1", "2", "3", "4"],
                    id = "regression-endq-dropdown"
                )
                
            ],
            className="mb-3", style={'width': '48%', 'float': 'left', 'display': 'inline-block', 'margin': '10'}
        ),

        html.Div(
            [
                dbc.Button("Regress", id= "btn-regress", style={"margin-top": 10, "margin-right": 10, "display":"inline"}, className="ms-auto", n_clicks=0),
            ]
        ),
    ],
    body=True
)

#Visualization tab help button
modal_viz = dbc.Modal([
                dbc.ModalHeader(dbc.ModalTitle("Information"), close_button=True),
                dbc.ModalBody([
                    html.H4("Function"),
                    html.P(
                    """
                    This tab visualizes data from the global dataset of historical revenue,
                    inventory, and capex data for the following Intel Competitors: TSMC, SMIC, 
                    UMC, GlobalFoundries. The data can be visualized by several metrics individually 
                    and combo charts can be created for submetric comparisons. Additionally, for individually
                    displayed data, forecasting using machine learning models can be enabled to estimate
                    future growth of the selected metric/submetric."""),
                    html.H4("Instructions"),
                    html.P(["1) Select an Intel competitor: TSMC, SMIC, UMC, or GFS.", html.Br(),
                    "2) Select a metric's data to visualize: Revenue, Inventory, CapEx, Revenue by Geography, Revenue by Segment, Revenue by Technology", html.Br(),
                    "3) If Rev by Geo, Segment, or Tech is selected, user has option to select how to visualize this data. See Additional Info for differences between visualization styles", html.Br(),
                    "4) (Optional) If an individual visualization style is chosen, user can select which submetric to visualize", html.Br(),
                    "5) Select time range to visualize data for using yera and quarter drop downs (These will be limited for the years and quarters that data currently exists for, for chosen options)", html.Br(),
                    "6) (Optional) If a single metric of submetric is visualized, user can turn on forecasting switch to forecast data for # of years indicated in the 'Years to Forecast' dropdown", html.Br(),
                    "7) (Optional) Download data that is displayed by clicking 'Download Data' button, and download chart visualization by clicking camera icon on top right of visualization"]),
                    html.H4("Output"),
                    html.P([
                    "• Chart visualization for time range and metrics chosen for selected company", html.Br(),
                    "• Data table with filtered data used to display visualization", html.Br()
                    ]),
                    html.H4("Additional Info"),
                    html.P([
                    "• [Visualization Style] Comparison visualization style will display stacked barchart when comparing by %, and a multi line chart when visualizing by absolute revenue.", html.Br(),
                    "• [Visualization Style] Individual visualization style will display line chart for both percent and by revenue, but forecasting can only be enabled when displaying by revenue.", html.Br(),
                    "• Data visualization are limited by data that exists in global dataset, so it is possible that certain quarters may be skipped in the visualization.", html.Br(),
                    "• CAGR over the period chosen is displayed in title of the chart", html.Br(),
                    "• Hovering over each point on the data visualization will display the Quarter over Quarter growth %, but this is growth from last quarter that exists in the dataset and is displayed ", html.Br(),
                    ]),
                     ]
                ),
                dbc.ModalFooter(
                    dbc.Button(
                        "Close",
                        id="close-viz",
                        className="ms-auto",
                        n_clicks=0,
                    )
                ),
            ],
            id="modal-viz",
            scrollable=True,
            is_open=False,
        )

#Scraping tab help button
modal_scraping = dbc.Modal([
                dbc.ModalHeader(dbc.ModalTitle("Information"), close_button=True),
                dbc.ModalBody([
                    html.H4("Function"),
                    html.P(
                    """
                    This tab scrapes quarterly PDF reports from companies and adds the data
                    to the global data set. Additionally, this tab provides a manual option to input data."""),
                    html.H4("Automatic Scraper Instructions"),
                    html.P(["1) Enter URL to PDF for Intel Competitor that needs to be scraped.", html.Br(),
                    "2) Select from TSMC, SMIC, UMC, GFS to idetify the company that the Quarterly Report is for.", html.Br(),
                    "3) Select year and quarter of the inputted quarterly report.", html.Br(),
                    "4) Click 'Scrape PDF', and see the scraped data on the right side of the tab.", html.Br(),
                    "5) Click 'Approve' if the data appears to be scraped properly, 'Reject' if the data looks incorrect, and 'Undo' if 'Approve' was accidentally clicked.", html.Br(),]),
                    html.H4("Manual Input Instructions"),
                    html.P([
                    "1) Select Company, Year, and Quarter, to see tables of metrics and submetrics to fill out.", html.Br(),
                    "2) Change any data labels if labels have changed from previous quarter, and after adding all data click 'Approve' to add to data set.", html.Br(),
                    "3) Click 'Undo' if data is accidentally added."]),
                    html.H4("Output"),
                    html.P([
                    "Data table of data that will be inputted into global data set that can be visualized in data visualization tab."
                    ]),
                    html.H4("Additional Info"),
                    html.P([
                    "• URL must be a valid quarterly report for selected company or parsing will fail.", html.Br(),
                    "• If quarterly report format changes drasticaly, parsing support might end for selected companies future reports.", html.Br(),
                    "• All fields in manual data input must be filled to add to data set, user can delete rows for fields that no longer exist."
                    ]),
                     ]
                ),
                dbc.ModalFooter(
                    dbc.Button(
                        "Close",
                        id="close-scraping",
                        className="ms-auto",
                        n_clicks=0,
                    )
                ),
            ],
            id="modal-scraping",
            scrollable=True,
            is_open=False,
        )

#Pulling tab help button
modal_pulling = dbc.Modal([
                dbc.ModalHeader(dbc.ModalTitle("Information"), close_button=True),
                dbc.ModalBody([
                    html.H4("Function"),
                    html.P(
                    "Extracts the past 5 years of revenue data for companies listed on US stock exchanges using the Alpha Vantage API. Saves pulled data to revenue.csv in the project directory."),
                    html.H4("Instructions"),
                    html.P(["1) (Optional) Add or remove a list of comma-separated tickers. Adding tickers does not automatically pull them.", html.Br(),
                    "2) (Optional) Select 1+ company tickers to pull revenue for.", html.Br(),
                    "3) Click 'Update Select Tickers' to pull revenue for companies in the 'Company Tickers' field. Click 'Update All Tickers' to update all ticker options in 'Company Tickers'", html.Br()]),
                    html.H4("Output"),
                    html.P([
                    "Data table with 1 quarter of revenue data per company per row."
                    ]),
                    html.H4("Additional Info"),
                    html.P([
                    "• Tickers must be listed on a US stock exchange (NYSE, NASDAQ), or they will cause an error.", html.Br(),
                    "• Once a ticker option is added, it will be available the next time the dashboard is opened.", html.Br(),
                    "• All tickers must be pulled once per quarter to update the revenue dataset.", html.Br(),
                    "• Alpha Vantage API limits calls to 5 calls per minute. The program automatically waits until the next 5 companies can be pulled. Please keep the dashboard open while data is pulled.", html.Br(),
                    "• When pulling more than 5 tickers, unexpected errors may occur due to the call limit. Wait at least 10 seconds and pull again.", html.Br(),
                    "• The revenue will be in the same currency as the company's income statement. Our program automatically converts NTD to USD."
                    ]),
                    ]
                ),
                dbc.ModalFooter(
                    dbc.Button(
                        "Close",
                        id="close-pulling",
                        className="ms-auto",
                        n_clicks=0,
                    )
                ),
            ],
            id="modal-pulling",
            scrollable=True,
            is_open=False,
        )

#Regression tab help button
modal_regression = dbc.Modal([
                dbc.ModalHeader(dbc.ModalTitle("Information"), close_button=True),
                dbc.ModalBody([
                    html.H4("Function"),
                    html.P(
                    """
                    Applies multiple linear regression to estimate the relationship 
                    between 1 Intel competitor's revenue segment and 1+ predictor companies' revenue."""),
                    html.H4("Instructions"),
                    html.P(["1) Select an Intel competitor: TSMC, SMIC, UMC, or GFS.", html.Br(),
                    "2) Select 1 competitor revenue segment to regress on.", html.Br(),
                    "3) Select 1+ predictor companies to regress on.", html.Br(),
                    "4) Select the years and quarters in order: Starting Year, Starting Quarter, Ending Year, Ending Quarter."]),
                    html.H4("Output"),
                    html.P([
                    "The regression model outputs 2 graphs:", html.Br(),
                    "• The line graph compares the model's predicted values of the competitor's percent change in segment revenue quarter on quarter versus the actual percent change.", html.Br(),
                    "• The bar graph visualizes the linear coefficient for each predictor company, and shows the strength and direction of the relationship between the competitor and predictor."
                    ]),
                    html.H4("Additional Info"),
                    html.P(["• All dropdowns are configured to only display options with available data.", html.Br(),
                     "• The available predictor companies are those whose revenue have been pulled on the 'Pulling' tab. To add predictor company options, add a custom ticker on the 'Pulling' tab and pull its revenue."
                    ]),
                    ]
                ),
                dbc.ModalFooter(
                    dbc.Button(
                        "Close",
                        id="close-regression",
                        className="ms-auto",
                        n_clicks=0,
                    )
                ),
            ],
            id="modal-regression",
            scrollable=True,
            is_open=False,
        )

#Displays Intel logo in navigation bar
navbar = dbc.Navbar(
    dbc.Container(
        [
            html.A(
                dbc.Row(
                    [
                        dbc.Col(html.Img(src=app.get_asset_url('intellogo.png'), height="40px", width="auto")),
                    ],
                    align="center",
                    className="g-0",
                ),
                style={"textDecoration": "none"},
            ),
        ],
        fluid=True
    ),
    style={"margin-bottom":10}
)

#Layout of dashboard, aggregates all the visual components
app.layout = html.Div([
    navbar,
    dbc.Tabs([
        dbc.Tab(label="Visualization", children=[
        dbc.Container(
            [
                html.Div([modal_viz]),
                html.Div([
                html.H2("Competitor Visualizations", style={'width': '48%', 'display': 'inline', "margin":20, "margin-left":0}),
                html.Button("?", id= "open-viz", style=roundbutton)],
                style={"margin":20}
                ),
                html.Hr(),
                dbc.Row(
                    [
                        dbc.Col(controls, md=4, align='start'),
                        dbc.Col([
                            dcc.Graph(id="graph"),
                            html.Div(
                            dash_table.DataTable(
                                data=[],
                                id="df-viz",
                                style_table={
                                    'height': 400,
                                    'overflowY': 'scroll'
                                }
                                ),
                                id="data-table-block",
                                style={"display":"none"},
                            )
                            ],
                            md=8),
                    ],
                    align="center",
                ),
            ],
            fluid=True,
        )
        ]),
        dbc.Tab(label="Scraping", children=[
        dbc.Container(
            [
                html.Div([modal_scraping]),
                html.Div([
                html.H2("Competitor Parsing", style={'width': '48%', 'display': 'inline', "margin":20, "margin-left":0}),
                html.Button("?", id= "open-scraping", style=roundbutton)],
                style={"margin":20}
                ),
                html.Hr(),
                dbc.Row(
                    [
                        dbc.Col(parsing, md=4, align='start'),
                        dbc.Col(
                            [
                                html.Div(
                                    dash_table.DataTable(data=[], id="df-scraped", style_cell={"margin-bottom":10}),
                                    id = 'auto-parsing-dt',
                                    style = {"display":"inline"},
                                ),
                                html.Div(
                                    [
                                    dash_table.DataTable(
                                        id = 'manual-dt',
                                        columns=(
                                            [{'id': 'revenue','name':'Revenue ($USD)'}]+
                                            [{'id': 'inventory','name':'Inventory ($USD)'}]+
                                            [{'id': 'capex','name':'Capex ($USD)'}]+
                                            [{'id': 'gross_margin','name':'Gross Margin (%)'}]
                                        ),
                                        data=[
                                            {'column-{}'.format(i): (j + (i-1)*3) for i in range(1, 3)}
                                            for j in range(1)
                                        ],
                                        editable=True
                                    ),
                                    dash_table.DataTable(
                                        id = 'seg-submetrics-dt',
                                        columns=(
                                            [{'id': 'rev-seg','name':'Revenue by Segment Submetric'}]+
                                            [{'id': 'rev-seg-value','name':'Percent (%)'}]
                                        ),
                                        data=[
                                            {'column-{}'.format(i): (j + (i-1)*5) for i in range(1, 5)}
                                            for j in range(5)
                                        ],
                                        editable=True,
                                        row_deletable=True
                                    ),
                                    dbc.Button('Add Row', id='seg-rows', className="ms-auto", style={"margin-top":10, "margin-bottom":10}, n_clicks=0),
                                    dash_table.DataTable(
                                        id = 'tech-submetrics-dt',
                                        columns=(
                                            [{'id': 'rev-tech','name':'Revenue by Technology Submetric'}]+
                                            [{'id': 'rev-tech-value','name':'Percent (%)'}]
                                        ),
                                        data=[
                                            {'column-{}'.format(i): (j + (i-1)*5) for i in range(1, 5)}
                                            for j in range(5)
                                        ],
                                        editable=True,
                                        row_deletable=True
                                    ),
                                    dbc.Button('Add Row', id='tech-rows', className="ms-auto", style={"margin-top":10, "margin-bottom":10}, n_clicks=0),
                                    dash_table.DataTable(
                                        id = 'geo-submetrics-dt',
                                        columns=(
                                            [{'id': 'rev-geo','name':'Revenue by Geographic Submetric'}]+
                                            [{'id': 'rev-geo-value','name':'Percent (%)'}]
                                        ),
                                        data=[
                                            {'column-{}'.format(i): (j + (i-1)*5) for i in range(1, 5)}
                                            for j in range(5)
                                        ],
                                        editable=True,
                                        row_deletable=True
                                    ),
                                    dbc.Button('Add Row', id='geo-rows', className="ms-auto", style={"margin-top":10}, n_clicks=0),
                                    ],
                                    id='manual-input',
                                    style={"display":"none"},
                                ),
                                manual_buttons,
                                buttons
                            ]
                            , md=8)
                    ],
                    align="center",
                ),
            ],
            fluid=True,
        )
        ]),
        dbc.Tab(label="Pulling", children=[
            dbc.Container([
                html.Div([modal_pulling]),
                html.Div([
                html.H2("Revenue Extraction", style={'width': '48%', 'display': 'inline', "margin":20, "margin-left":0}),
                html.Button("?", id= "open-pulling", style=roundbutton)],
                style={"margin":20}
                ),
                html.Hr(),
                dbc.Row(
                    [
                        dbc.Col(puller, md=4, align='start'),
                        dbc.Col(
                            [dash_table.DataTable(
                                data=[],
                                id="df-pulled",
                                style_table={
                                    'height': 600,
                                    'overflowY': 'scroll',
                                    'overflowX': 'scroll'
                                }
                                )
                            ],
                            md=8
                        )
                    ],
                    align="center",
                ),
            ],
            fluid=True
            )
        ],
        ),

        dbc.Tab(label="Regression", children=[
            dbc.Container([
                html.Div([modal_regression]),
                html.Div([
                    html.H2("Competitor Regression", style={'width': '48%', 'display': 'inline', "margin":20, "margin-left":0}),
                    html.Button("?", id= "open-regression", style=roundbutton),
                    ],
                    style={"margin":20}
                    ),
                html.Hr(),
                dbc.Row(
                    [
                        dbc.Col(regression, md=4, align='start'),
                        dbc.Col([
                                html.Div([
                                    dcc.Graph(id="regression-graph1"),
                                    dcc.Graph(id="regression-graph2"),
                                    ],
                                    id="regression-graph-block",
                                    style={"display":"none"}
                                ),
                                html.Div(
                                dash_table.DataTable(
                                    data=[],
                                    id="df-regression",
                                    style_table={
                                        'height': 400,
                                        'overflowY': 'scroll'
                                    }
                                    ),
                                    id="regression-table-block",
                                    style={"display":"none"},
                                )
                            ],
                            md=8
                        )
                    ],
                    align="center",
                ),
            ],
            fluid=True
            )
        ],
        )
    ])
])

#VISUALIZATION TAB CALLBACKS
'''Returns metric dropdown options depending on the selected company's available data'''
@app.callback(
    Output("metric-dropdown","options"),
    Input("company-dropdown", "value")
)
def set_metric(company):
    if company:
        local_df = global_df
        local_df = local_df.loc[(local_df["company"] == company)]
        metrics = local_df["metric"].dropna().unique()
        metrics = [var_to_metric[m] for m in metrics]
        return metrics
    return ["Revenue by Technology", "Revenue by Segment", "Revenue by Geography", "CapEx", "Inventory", "Revenue", "Gross Margin"]

'''Returns visualization style options depending on the selected company's available data'''
@app.callback(
    Output("viz-dropdown","options"),
    Output("viz-dropdown","value"),
    Input("metric-dropdown","value")
)
def visualization_options(metric):
    if metric != "CapEx" and metric != "Inventory" and metric != "Revenue" and metric != "Gross Margin" and metric != None:
        return ["Comparison (Percent)","Comparison (Revenue)","Individual (Percent)", "Individual (Revenue)"],"Comparison (Percent)"
    else:
        return [],None

'''Returns submetric dropdown options depending on the selected company's available data'''
@app.callback(
    Output("submetric-dropdown","options"),
    Input("company-dropdown","value"),
    Input("metric-dropdown","value"),
    Input("viz-dropdown","value")
)
def set_submetric(company,metric,viz):
    if viz == "Comparison (Percent)" or viz == "Comparison (Revenue)" or viz == None:
        return []
    else:
        local_df = global_df
        local_df = local_df.loc[(local_df["company"] == company) & (local_df["metric"] == metric_to_var[metric])]
        return local_df["sub-metric"].dropna().unique()

'''Returns starting year options depending on the selected company's available data'''
@app.callback(
    Output("start-dropdown","options"),
    Input("company-dropdown","value"),
    Input("metric-dropdown","value"),
    Input("submetric-dropdown", "value"),
)
def set_start_year(company,metric,submetric):
    if all([company, metric]):
        local_df = global_df
        local_df = local_df.loc[(local_df["company"] == company) & (local_df["metric"] == metric_to_var[metric])]
        if submetric:
            local_df = local_df.loc[(local_df["sub-metric"] == submetric)]
        years = local_df["year"].dropna().unique()
        return np.sort(years)
    return np.arange(firstYear, currYear)

'''Returns starting quarter options depending on the selected company's available data'''
@app.callback(
    Output("startq-dropdown","options"),
    Input("company-dropdown","value"),
    Input("metric-dropdown","value"),
    Input("submetric-dropdown", "value"),
    Input("start-dropdown","value")
)
def set_start_quarter(company,metric,submetric, startYear):
    if all([company, metric, startYear]):
        local_df = global_df
        local_df = local_df.loc[(local_df["company"] == company) & (local_df["metric"] == metric_to_var[metric]) & (local_df["year"] == startYear)]
        if submetric:
            local_df = local_df.loc[(local_df["sub-metric"] == submetric)]
        quarters = local_df["quarter"].dropna().unique()
        return np.sort(quarters)
    return [1, 2, 3, 4]

'''Returns ending year options depending on the selected company's available data'''
@app.callback(
    Output("end-dropdown","options"),
    Input("company-dropdown","value"),
    Input("metric-dropdown","value"),
    Input("submetric-dropdown", "value"),
    Input("start-dropdown", "value"),
)
def set_end_year(company,metric,submetric,startYear):
    if all([company, metric, startYear]):
        local_df = global_df
        local_df = local_df.loc[(local_df["company"] == company) & (local_df["metric"] == metric_to_var[metric])]
        if submetric:
            local_df = local_df.loc[(local_df["sub-metric"] == submetric)]
        years = local_df.loc[(local_df["year"]) >= startYear]["year"].dropna().unique()
        return np.sort(years)
    return np.arange(firstYear, currYear)

'''Returns ending quarter options depending on the selected company's available data'''
@app.callback(
    Output("endq-dropdown","options"),
    Input("company-dropdown","value"),
    Input("metric-dropdown","value"),
    Input("submetric-dropdown", "value"),
    Input("start-dropdown", "value"),
    Input("startq-dropdown", "value"),
    Input("end-dropdown", "value"),
)
def set_end_quarter(company,metric,submetric,startYear,startQuarter,endYear):
    if all([company, metric, startYear, startQuarter, endYear]):
        local_df = global_df
        local_df = local_df.loc[(local_df["company"] == company) & (local_df["metric"] == metric_to_var[metric])]
        if submetric:
            local_df = local_df.loc[(local_df["sub-metric"] == submetric)]
        quarters = local_df.loc[local_df["year"] == endYear]["quarter"].dropna().unique()
        if startYear == endYear:
            quarters = [q for q in quarters if q >= startQuarter]
        return np.sort(quarters)
    return [1, 2, 3, 4]

'''Creates graphs on visualization tab, returns data table used in the graph'''
@app.callback(
    Output("graph", "figure"),
    Output("dataframe","data"),
    Output("df-viz", "data"),
    Output("df-viz", "columns"),
    Output("data-table-block","style"),
    [
        Input("company-dropdown", "value"),
        Input("metric-dropdown", "value"),
        Input("viz-dropdown", "value"),
        Input("submetric-dropdown", "value"),
        Input("start-dropdown", "value"),
        Input("startq-dropdown", "value"),
        Input("end-dropdown", "value"),
        Input("endq-dropdown", "value"),
        Input("forecasting-switch", "on"),
        Input("forecasting-dropdown", "value"),
    ],
    prevent_initial_call=True,
)
def make_graph(company, metric, viz, submetric, start_year, start_quarter, end_year, end_quarter,forecast_check,forecast_years):
    if metric == "CapEx" or metric == "Inventory" or metric == "Revenue" or metric == "Gross Margin":
        submetric = None
    graph = go.Figure()
    graph.update_layout(
        xaxis =  { "visible": False },
        yaxis = { "visible": False },
        annotations = [
            {   
                "text": "Data does not exist for selected time span. Choose different range.",
                "xref": "paper",
                "yref": "paper",
                "showarrow": False,
                "font": {
                    "size": 16
                }
            }
        ]
    )
    if start_year == None or start_quarter == None or end_year == None or end_quarter == None:
        return graph, {}, np.array([]) ,[], {"display":"none"}

    local_df = global_df
    local_df = local_df.loc[(local_df["company"] == company) & (local_df["metric"] == metric_to_var[metric])]
    rev_df = global_df.loc[(global_df["company"] == company) & (global_df["metric"] == metric_to_var["Revenue"])]
    rev_df["quarter-string"] = rev_df["year"].map(lambda x: str(x)[-2:]) + "Q" + rev_df["quarter"].map(str)
    if (submetric != None or submetric != "NaN") and (viz == "Individual (Percent)" or viz == "Individual (Revenue)"):
        local_df = local_df.loc[local_df["sub-metric"] == submetric]
    rev_df = rev_df.sort_values(by=["quarter-string"])
    local_df["quarter-string"] = local_df["year"].map(lambda x: str(x)[-2:]) + "Q" + local_df["quarter"].map(str)
    local_df = local_df.sort_values(by=["quarter-string"])
    start_q = join_quarter_year(start_quarter, start_year)
    end_q = join_quarter_year(end_quarter, end_year)

    try:  
        index_start = local_df["quarter-string"].tolist().index(start_q)
        index_start2 = rev_df["quarter-string"].tolist().index(start_q)
        index_end = len(local_df["quarter-string"].tolist()) - local_df["quarter-string"].tolist()[::-1].index(end_q) - 1
        index_end2 = len(rev_df["quarter-string"].tolist()) - rev_df["quarter-string"].tolist()[::-1].index(end_q) - 1
    except ValueError:
        return graph, {}, np.array([]) ,[], {"display":"none"}

    filtered_data = local_df.iloc[index_start:index_end + 1]
    rev_filtered = rev_df.iloc[index_start2:index_end2 + 1]
    filtered_data.loc[:,("value")] = filtered_data["value"].astype(float).round(2)
    rev_filtered = rev_filtered[["quarter-string", "value"]]
    rev_filtered.columns = ["quarter-string","revenue"]
    last_index_array = len(filtered_data["value"].tolist())-1
    filtered_data["quarter"] = pd.to_numeric(filtered_data["quarter"])
    filtered_data["year"] = pd.to_numeric(filtered_data["year"])
    filtered_data["value"] = pd.to_numeric(filtered_data["value"])
    quarter_diff = filtered_data["quarter"].tolist()[last_index_array] - filtered_data["quarter"].tolist()[0] + 1
    number_quarters = filtered_data["year"].tolist()[last_index_array] - filtered_data["year"].tolist()[0] + quarter_diff
    cagr = round(abs(pow((filtered_data["value"].tolist()[last_index_array]/ (filtered_data["value"].tolist()[0]+0.00001)),1/number_quarters) - 1) * 100,2)
    filtered_data = filtered_data.sort_values(by=["year","quarter"])
    if viz == "Comparison (Percent)":
        graph = px.bar(filtered_data, x="quarter-string", y="value",
        color="sub-metric",
        labels={
                "quarter-string": "Quarters",
                "value": "Percentage %",
                "sub-metric": f'{metric.split()[-1]}'
            },
        title=f'{metric} for {company} from {start_q} to {end_q}')
        graph.update_layout(barmode='stack',xaxis={'categoryorder':'array', 'categoryarray':[filtered_data['quarter-string']]})
    elif viz == "Comparison (Revenue)":
        filtered_data = filtered_data.join(rev_filtered.set_index('quarter-string'), on='quarter-string')
        filtered_data["rev"] = [round(a*b,2) for a,b in zip([float(x)/100 for x in filtered_data["value"].tolist()],[float(x) for x in filtered_data["revenue"].tolist()])]
        graph = px.line(filtered_data, x="quarter-string", y="rev",
        color="sub-metric",
        labels={
                "quarter-string": "Quarters",
                "rev": "US$ Dollars (Millions)",
                "sub-metric": f'{metric.split()[-1]}'
            },
        title=f'{metric} for {company} from {start_q} to {end_q}')
    #individual metrics
    elif submetric == None or submetric == "NaN":
        if metric == "Gross Margin":
            filtered_data["value_percent"] = filtered_data["value"].apply(lambda x: str(x)+"%")
            graph = px.line(filtered_data, x="quarter-string", y="value",
            labels={
            "quarter-string": "Quarters",
            "value": "Percentage %",
                },
            hover_data=["quarter-string", "value"],
            title=f'{metric} for {company} from {start_q} to {end_q}', markers=True)
        elif forecast_check == True:
            forecast_data = filtered_data.drop(["quarter-string","metric"],axis=1)
            forecast = fut_forecast(forecast_data,int(forecast_years))
            fig = plot_plotly(forecast[0], forecast[1], xlabel="Date", ylabel="Value of Metric")
            graph = fig
        else:
            filtered_data["QoQ"] = filtered_data.value.pct_change().mul(100).round(2)
            filtered_data["QoQ"] = filtered_data["QoQ"].apply(lambda x: str(x)+"%")
            graph = px.line(filtered_data, x="quarter-string", y="value",
            labels={
            "quarter-string": "Quarters",
            "value": "US$ Dollars (Millions)",
                },
            hover_data=["quarter-string", "value","QoQ"],
            title=f'{metric} for {company} from {start_q} to {end_q}, CAGR = {cagr}%', markers=True)
    #individual submetric
    else:
        filtered_data["QoQ"] = filtered_data.value.pct_change().mul(100).round(2)
        filtered_data["QoQ"] = filtered_data["QoQ"].apply(lambda x: str(x)+"%")
        #Graph for individual submetric by percent
        if viz == "Individual (Percent)":
            graph = px.line(filtered_data, x="quarter-string", y="value",
            labels={
            "quarter-string": "Quarters",
            "value": "Percentage %",
                },
            hover_data=["quarter-string", "value","QoQ"],
            title=f'{metric}: {submetric} for {company} from {start_q} to {end_q}, CAGR = {cagr}%', markers=True)
        #Graph for individual submetric in dollars
        else:
            filtered_data = filtered_data.join(rev_filtered.set_index('quarter-string'), on='quarter-string')
            filtered_data["rev"] = [round(a*b,2) for a,b in zip([float(x)/100 for x in filtered_data["value"].tolist()],[float(x) for x in filtered_data["revenue"].tolist()])]
            filtered_data["value"] = filtered_data["rev"]
            if forecast_check == True:
                forecast_data = filtered_data.drop(["quarter-string","metric","revenue","rev","QoQ"],axis=1)
                forecast = fut_forecast(forecast_data,int(forecast_years))
                fig = plot_plotly(forecast[0], forecast[1], xlabel="Date", ylabel="Value of Metric")
                graph = fig
            else:
                graph = px.line(filtered_data, x="quarter-string", y="rev",
                labels={
                "quarter-string": "Quarters",
                "value": "US$ Dollars (Millions)",
                    },
                hover_data=["quarter-string", "value","QoQ"],
                title=f'{metric}: {submetric} for {company} from {start_q} to {end_q}. CAGR = {cagr}%', markers=True)

    return graph,filtered_data.to_dict(), filtered_data.to_dict('records'), [{"name": i, "id": i} for i in filtered_data.columns], {"display":"inline"}

'''Download data from visualization tab'''
@app.callback(
    Output("download-data-csv","data"),
    Input("btn-data","n_clicks"),
    Input("dataframe","data"),
    prevent_initial_call=True,
)
def export_graph(n_clicks,dataframe):
    changed_id = [p['prop_id'] for p in callback_context.triggered][0]
    if 'btn-data' in changed_id:
        return dcc.send_data_frame(pd.DataFrame(dataframe).to_csv, EXPORT_FILE)
    return None

'''Displays visualization tab help button'''
@app.callback(
    Output("modal-viz", "is_open"),
    [Input("open-viz", "n_clicks"), Input("close-viz", "n_clicks")],
    [State("modal-viz", "is_open")],
)
def toggle_modal_viz(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

#SCRAPING TAB CALLBACKS
'''Automatic scraper on scraping tab, returns table of scraped data and action buttons'''
@app.callback(
    Output("btn-approve","style"),
    Output("btn-reject","style"),
    Output("btn-undo","style"),
    Output("confirmation-msg","style"),
    Output("df-scraped", "data"),
    Output("df-scraped", "columns"),
    Output("json-store","data"),
    Input("url-input","value"),
    Input("company-input","value"),
    Input("year-input","value"),
    Input("quarter-input","value"),
    Input("btn-scrape", "n_clicks"),
    prevent_initial_call=True,
)
def scrape_pdf(url, company, year, quarter, click):
    changed_id = [p['prop_id'] for p in callback_context.triggered][0]
    if 'btn-scrape' in changed_id:
        abbrev = company_abbrev[company]
        new_json = scraper.pull(url, quarter, year, abbrev)
        new_df = pd.DataFrame.from_dict(new_json)
        return {"display":"inline"}, {"display":"inline"}, {"display":"inline"}, {"display":"block"}, new_df.to_dict('records'), [{"name": i, "id": i} for i in new_df.columns], new_json
    new_df = pd.DataFrame()
    return {"display":"none"}, {"display":"none"}, {"display":"none"}, {"display":"none"}, new_df.to_dict('records'), [{"name": i, "id": i} for i in new_df.columns], {}

'''Enables manual input on scraping tab, returns blank tables'''
@app.callback(
    Output("btn-add","style"),
    Output("btn-undo-manual","style"),
    Output("confirmation-msg2","style"),
    Output("manual-input","style"),
    Output("seg-submetrics-dt","data"),
    Output("tech-submetrics-dt","data"),
    Output("geo-submetrics-dt","data"),
    Output("manual-dt","columns"),
    Output("auto-parsing-dt","style"),
    Output("auto-parsing-buttons","style"),
    Input("manual-company-input","value"),
    Input("manual-year-input","value"),
    Input("manual-quarter-input","value"),
    Input("btn-manual","n_clicks"),
    Input("seg-submetrics-dt","columns"),
    Input("tech-submetrics-dt","columns"),
    Input("geo-submetrics-dt","columns"),
    Input('seg-rows', 'n_clicks'),
    State("seg-submetrics-dt", 'data'),
    Input('tech-rows', 'n_clicks'),
    State("tech-submetrics-dt", 'data'),
    Input('geo-rows', 'n_clicks'),
    State("geo-submetrics-dt", 'data'),
    prevent_initial_call=True
)
def manual_input_dfs(company,year,quarter,click,columns1,columns2,columns3,seg_clicks,sr,tech_clicks,tr,geo_clicks,gr):
    columns4=(
        [{'id': 'revenue','name':'Revenue ($USD)'}]+
        [{'id': 'inventory','name':'Inventory ($USD)'}]+
        [{'id': 'capex','name':'Capex ($USD)'}] +
        [{'id': 'gross_margin','name':'Gross Margin (%)'}]
    )
    changed_id = [p['prop_id'] for p in callback_context.triggered][0]
    if 'btn-manual' in changed_id:
        local_df = global_df.loc[global_df["company"] == company]
        last_year = local_df.sort_values(by='year',ascending=False)["year"].tolist()[0]
        last_quarter = local_df.sort_values(by='year',ascending=False)["quarter"].tolist()[0]
        local_df = local_df.loc[(local_df["year"] == last_year) & (local_df["quarter"] == last_quarter)]
        rev_seg = local_df.loc[local_df["metric"] == metric_to_var["Revenue by Segment"]]["sub-metric"].dropna().unique()
        rev_tech = local_df.loc[local_df["metric"] == metric_to_var["Revenue by Technology"]]["sub-metric"].dropna().unique()
        rev_geo = local_df.loc[local_df["metric"] == metric_to_var["Revenue by Geography"]]["sub-metric"].dropna().unique()
        rev_seg_data = [
            dict({"rev-seg":rev_seg[j]}, **{c['id']: None for c in columns1[1:]}) for j in range(len(rev_seg))
        ]
        tech_seg_data = [
            dict({"rev-tech":rev_tech[j]}, **{c['id']: None for c in columns2[1:]}) for j in range(len(rev_tech))
        ]
        geo_seg_data = [
            dict({"rev-geo":rev_geo[j]}, **{c['id']: None for c in columns3[1:]}) for j in range(len(rev_geo))
        ]
        if company == "UMC" or company == "TSMC":
            columns4=(
                [{'id': 'revenue','name':'Revenue ($NT)'}]+
                [{'id': 'inventory','name':'Inventory ($NT)'}]+
                [{'id': 'capex','name':'Capex ($NT)'}]+
                [{'id': 'gross_margin','name':'Gross Margin (%)'}]
            )
        return {"display":"inline"}, {"display":"inline"}, {"display":"inline"},{"display":"inline"},rev_seg_data, tech_seg_data, geo_seg_data,columns4,{"display":"none"}, {"display":"none"}
    if 'seg-rows' in changed_id:
        sr.append({c['id']: None for c in columns1})
        return {"display":"inline"}, {"display":"inline"}, {"display":"inline"},{"display":"inline"}, sr,tr,gr,columns4,{"display":"none"}, {"display":"none"}
    if 'tech-rows' in changed_id:
        tr.append({c['id']: None for c in columns2})
        return {"display":"inline"}, {"display":"inline"}, {"display":"inline"},{"display":"inline"}, sr,tr,gr,columns4,{"display":"none"}, {"display":"none"}
    if 'geo-rows' in changed_id:
        gr.append({c['id']: None for c in columns3})
        return {"display":"inline"}, {"display":"inline"}, {"display":"inline"},{"display":"inline"}, sr,tr,gr, columns4,{"display":"none"}, {"display":"none"}
    return {"display":"none"}, {"display":"none"}, {"display":"none"},{"display":"none"}, sr,tr,gr,columns4,{"display":"inline"}, {"display":"inline"}

'''Updates global dataset when 'Approve', 'Reject', 'Undo' buttons are clicked for automatic scraping, returns confirmation message'''
@app.callback(
    Output("confirmation-msg","children"),
    Input("btn-approve","n_clicks"),
    Input("btn-reject","n_clicks"),
    Input("btn-undo","n_clicks"),
    Input("company-input","value"),
    Input("year-input","value"),
    Input("quarter-input","value"),
    Input("json-store","data"),
    prevent_initial_call=True,
)
def update_global(approve, reject, undo, company, year, quarter,json_store):
    changed_id = [p['prop_id'] for p in callback_context.triggered][0]
    quarter_year = join_quarter_year(quarter, year)

    if 'btn-reject' in changed_id:
        return 'Update has been rejected.'
    elif 'btn-approve' in changed_id: 
        old_data = pd.read_csv("data/data.csv").to_dict('records')
        json_store = pd.DataFrame.from_dict(json_store)
        if "sub-metric" not in json_store.columns:
            json_store.insert(4,"sub-metric","")
        json_store = json_store.to_dict('records')
        if json_store[-1] in old_data:
            return "Data already exists in the global dataset."
        else:
            pd.DataFrame.from_dict(json_store).to_csv('data/data.csv',mode='a',index=False,header=False)
            return f'{company} {quarter_year} has been added to the global dataset.'
    elif 'btn-undo' in changed_id:
        json_store = pd.DataFrame.from_dict(json_store)
        if "sub-metric" not in json_store.columns:
            json_store.insert(4,"sub-metric",np.nan)
        json_store = json_store.drop(columns="sub-metric")
        json_store = json_store.to_dict('records')
        current = pd.read_csv("data/data.csv").drop(columns="sub-metric").to_dict('records')
        current_df = pd.read_csv("data/data.csv")
        if json_store[-1] in current:
            current_df = current_df.iloc[:-(len(json_store)),:]
            current_df.to_csv('data/data.csv',mode='w',index=False)
            return "Data been removed from global dataset."
        else:
            return "There is nothing left to undo."
    return ""

'''Updates global dataset when 'Approve', 'Reject', or 'Undo' buttons are clicked for manual input, returns confirmation message'''
@app.callback(
    Output("confirmation-msg2","children"),
    Input("btn-add","n_clicks"),
    Input("btn-undo-manual","n_clicks"),
    Input("manual-company-input","value"),
    Input("manual-year-input","value"),
    Input("manual-quarter-input","value"),
    Input("manual-dt","data"),
    Input("seg-submetrics-dt","data"),
    Input("tech-submetrics-dt","data"),
    Input("geo-submetrics-dt","data"),
    Input("manual-dt","columns"),
    Input("seg-submetrics-dt","columns"),
    Input("tech-submetrics-dt","columns"),
    Input("geo-submetrics-dt","columns"),
    prevent_initial_call=True,
)
def upload_manual(add,undo,company,year,quarter,manual,seg,tech,geo,mc,sc,tc,gc):
    conv = converter.Converter()
    changed_id = [p['prop_id'] for p in callback_context.triggered][0]
    manual_df = pd.DataFrame(manual, columns=[c['id'] for c in mc])
    seg_df = pd.DataFrame(seg, columns=[c['id'] for c in sc])
    tech_df = pd.DataFrame(tech, columns=[c['id'] for c in tc])
    geo_df = pd.DataFrame(geo, columns=[c['id'] for c in gc])
    if 'btn-add' in changed_id:
        if not(manual_df.isnull().values.any()) and not(seg_df.isnull().values.any()) and not(tech_df.isnull().values.any()) and not(geo_df.isnull().values.any()):
            master_df = pd.DataFrame(data=[],columns=['metric','sub-metric','value'])
            seg_df.insert(0,'metric',"rev_seg")
            tech_df.insert(0,'metric',"tech_seg")
            geo_df.insert(0,'metric',"geo_seg")
            seg_df = seg_df.rename(columns={seg_df.columns[0]: "metric", seg_df.columns[1]: "sub-metric", seg_df.columns[2]: "value"})
            tech_df = tech_df.rename(columns={tech_df.columns[0]: "metric", tech_df.columns[1]: "sub-metric", tech_df.columns[2]: "value"})
            geo_df = geo_df.rename(columns={geo_df.columns[0]: "metric", geo_df.columns[1]: "sub-metric", geo_df.columns[2]: "value"})
            master_df = master_df.append(seg_df).append(tech_df).append(geo_df)
            master_df.insert(0,"quarter",quarter)
            master_df.insert(0,"year",year)
            master_df.insert(0,"company",company)
            metrics_df = pd.DataFrame({
                "company":company,
                "year":year,
                "quarter":quarter,
                "metric":["rev","inv","capex"],
                "sub-metric":['','',''],
                "value":[manual_df["revenue"].tolist()[0],manual_df["inventory"].tolist()[0],manual_df["capex"].tolist()[0]],
            })
            if company == "TSMC" or company == "UMC":
                metrics_df["value"] = metrics_df["value"].apply(lambda x: conv.twd_usd(x,year,quarter))
            gross_margin_df = pd.DataFrame({
                "company":company,
                "year":year,
                "quarter":quarter,
                "metric":["gross_margin"],
                "sub-metric":[''],
                "value":[manual_df["gross_margin"].tolist()[0]],
            })
            metrics_df = metrics_df.append(gross_margin_df)
            master_json = master_df.to_dict('records')
            metrics_json = metrics_df.to_dict('records')
            old_data = pd.read_csv("data/data.csv").to_dict('records')
            if metrics_json[-1] in old_data:
                return "Data already exists in the global dataset."
            else:
                master_df.to_csv('data/data.csv',mode='a',index=False,header=False)
                metrics_df.to_csv('data/data.csv',mode='a',index=False,header=False)
                return f'{company} {year} Q{quarter} has been added to the global dataset.'
        else:
            return "Unable to add to dataset. Certain values are blank."
    
    if 'btn-undo-manual' in changed_id:
        master_df = pd.DataFrame(data=[],columns=['metric','sub-metric','value'])
        seg_df.insert(0,'metric',"rev_seg")
        tech_df.insert(0,'metric',"tech_seg")
        geo_df.insert(0,'metric',"geo_seg")
        seg_df = seg_df.rename(columns={seg_df.columns[0]: "metric", seg_df.columns[1]: "sub-metric", seg_df.columns[2]: "value"})
        tech_df = tech_df.rename(columns={tech_df.columns[0]: "metric", tech_df.columns[1]: "sub-metric", tech_df.columns[2]: "value"})
        geo_df = geo_df.rename(columns={geo_df.columns[0]: "metric", geo_df.columns[1]: "sub-metric", geo_df.columns[2]: "value"})
        master_df = master_df.append(seg_df).append(tech_df).append(geo_df)
        master_df.insert(0,"quarter",quarter)
        master_df.insert(0,"year",year)
        master_df.insert(0,"company",company)
        metrics_df = pd.DataFrame({
            "company":company,
            "year":year,
            "quarter":quarter,
            "metric":["rev","inv","capex"],
            "sub-metric":['','',''],
            "value":[manual_df["revenue"].tolist()[0],manual_df["inventory"].tolist()[0],manual_df["capex"].tolist()[0]],
        })
        if company == "TSMC" or company == "UMC":
            metrics_df["value"] = metrics_df["value"].apply(lambda x: conv.twd_usd(x,year,quarter))
        gross_margin_df = pd.DataFrame({
                "company":company,
                "year":year,
                "quarter":quarter,
                "metric":["gross_margin"],
                "sub-metric":[''],
                "value":[manual_df["gross_margin"].tolist()[0]],
            })
        metrics_df = metrics_df.append(gross_margin_df)
        master_json = master_df.to_dict('records')
        metrics_json = metrics_df.to_dict('records')
        current = pd.read_csv("data/data.csv").to_dict('records')
        current_df = pd.read_csv("data/data.csv")
        if metris_json[-1] in current:
            current_df = current_df.iloc[:-(len(master_json)+len(metrics_json)),:]
            current_df.to_csv('data/data.csv',mode='w',index=False)
            return "Data been removed from global dataset."
        else:
            return "There is nothing left to undo."

'''Displays scraping tab help button'''
@app.callback(
    Output("modal-scraping", "is_open"),
    [Input("open-scraping", "n_clicks"), Input("close-scraping", "n_clicks")],
    [State("modal-scraping", "is_open")],
)
def toggle_modal_scraping(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

#PULLING TAB CALLBACKS
'''Adds or removes a comma-separated list of tickers to the ticker dropdown'''
@app.callback(
    Output("ticker-dropdown", "options"),
    Input("input-ticker", "value"),
    Input("btn-add-ticker", "n_clicks"),
    Input("btn-remove-ticker", "n_clicks"),
    Input("ticker-dropdown", "options"),
    prevent_initial_call=True,
)
def change_tickers(new_tickers, btnAdd, btnRemove, tickers):
    changed_id = [p['prop_id'] for p in callback_context.triggered][0]
    new_tickers = new_tickers.split(",")
    ticker_set = set(tickers)
    if 'btn-add-ticker' in changed_id:
        for t in new_tickers:
            t = t.upper()
            t = re.sub(r'[^A-Z]', '', t.upper())
            tickers.append(t) if t not in ticker_set else 'Ignore'
        with open(TICKER_FILE, "wb") as f:
            pickle.dump(tickers, f)
    elif 'btn-remove-ticker' in changed_id:
        for t in new_tickers:
            t = t.upper()
            t = re.sub(r'[^A-Z]', '', t.upper())
            if t in ticker_set:
                tickers.remove(t)
        with open(TICKER_FILE, "wb") as f:
            pickle.dump(tickers, f)
    return tickers

'''Pulls revenue for selected or all tickers from Alpha Vantage API, returns resulting data table'''
@app.callback(
    Output("df-pulled", "data"),
    Output("df-pulled", "columns"),
    Output("regression-ticker-dropdown", "options"),
    Input("ticker-dropdown", "value"),
    Input("ticker-dropdown", "options"),
    Input("btn-pull", "n_clicks"),
    Input("btn-update-all", "n_clicks"),
    Input("regression-ticker-dropdown", "options"),
    prevent_initial_call=True,
)
def pull_revenue(tickerVal, tickerOptions, btnPull, btnUpdate, regressionOptions):
    global revenue_df
    if btnPull + btnUpdate > 0:
        changed_id = [p['prop_id'] for p in callback_context.triggered][0]
        tickers = []
        if 'btn-pull' in changed_id:
            tickers = tickerVal
        elif 'btn-update-all' in changed_id:
            tickers = tickerOptions
        if tickers:
            new_df = stocks.get_revenue_list(tickers)
            revenue_df = pd.concat([revenue_df, new_df], axis=0)
            revenue_df = revenue_df.drop_duplicates()
            revenue_df.to_csv(REVENUE_FILE, index=False)
            new_df = new_df.round(2)
            return new_df.to_dict('records'), [{"name": i, "id": i} for i in new_df.columns], revenue_df["company"].unique()
    return [], [], regressionOptions

'''Displays pulling tab help button'''
@app.callback(
    Output("modal-pulling", "is_open"),
    [Input("open-pulling", "n_clicks"), Input("close-pulling", "n_clicks")],
    [State("modal-pulling", "is_open")],
)
def toggle_modal_pulling(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

#REGRESSION TAB CALLBACKS
'''Returns revenue segment dropdown options depending on the selected company's available data'''
@app.callback(
    Output("regression-segment-dropdown", "options"),
    Input("regression-comp-dropdown", "value"),
    prevent_initial_call=True
)
def display_segment(competitor):
    local_df = global_df.loc[global_df["company"] == competitor]
    return local_df["sub-metric"].dropna().unique()

'''Returns starting year options depending on the competitor's and predictors' available data'''
@app.callback(
    Output("regression-start-dropdown","options"),
    Input("regression-comp-dropdown","value"),
    Input("regression-segment-dropdown","value"),
    Input("regression-ticker-dropdown", "value"),
    prevent_initial_call=True,
)
def set_start_year_regress(competitor, submetric, predictors):
    if all([competitor, submetric, predictors]):
        local_df = global_df.loc[(global_df["company"] == competitor) & (global_df["sub-metric"] == submetric)]
        local_set = set(local_df["year"].unique())
        for p in predictors:
            local_set = local_set.intersection(set(revenue_df.loc[revenue_df["company"] == p]["year"].unique()))
        return sorted(list(local_set))
    return np.arange(firstYear, currYear)

'''Returns starting quarter options depending on the competitor's and predictors' available data'''
@app.callback(
    Output("regression-startq-dropdown","options"),
    Input("regression-comp-dropdown","value"),
    Input("regression-segment-dropdown","value"),
    Input("regression-ticker-dropdown", "value"),
    Input("regression-start-dropdown","value"),
    prevent_initial_call=True
)
def set_start_quarter_regress(competitor, submetric, predictors, startYear):
    if all([competitor, submetric, predictors, startYear]):
        local_df = global_df.loc[(global_df["company"] == competitor) & (global_df["sub-metric"] == submetric) & (global_df["year"] == startYear)]
        quarters = set(local_df["quarter"].dropna().unique())
        for p in predictors:
            quarters = quarters.intersection(set(revenue_df.loc[(revenue_df["company"] == p) & (revenue_df["year"] == startYear)]["quarter"]))
        return sorted(list(quarters))
    return [1, 2, 3, 4]

'''Returns ending year options depending on the competitor's and predictors' available data'''
@app.callback(
    Output("regression-end-dropdown","options"),
    Input("regression-comp-dropdown","value"),
    Input("regression-segment-dropdown","value"),
    Input("regression-ticker-dropdown", "value"),
    Input("regression-start-dropdown","value"),
    prevent_initial_call=True
)
def set_end_year_regress(competitor, submetric, predictors, startYear):
    if all([competitor, submetric, predictors, startYear]):
        local_df = global_df.loc[(global_df["company"] == competitor) & (global_df["sub-metric"] == submetric)]
        years = set(local_df.loc[(local_df["year"]) >= startYear]["year"].unique())
        for p in predictors:
            years = years.intersection(set(revenue_df.loc[(revenue_df["company"] == p) & (revenue_df["year"] >= startYear)]["year"]))
        return sorted(list(years))
    return np.arange(firstYear, currYear)

'''Returns ending quarter options depending on the competitor's and predictors' available data'''
@app.callback(
    Output("regression-endq-dropdown","options"),
    Input("regression-comp-dropdown","value"),
    Input("regression-segment-dropdown","value"),
    Input("regression-ticker-dropdown", "value"),
    Input("regression-start-dropdown","value"),
    Input("regression-startq-dropdown","value"),
    Input("regression-end-dropdown","value"),
    prevent_initial_call=True
)
def set_end_quarter_regress(competitor, submetric, predictors, startYear, startQuarter, endYear):
    if all([competitor, submetric, predictors, startYear, startQuarter, endYear]):
        local_df = global_df.loc[(global_df["company"] == competitor) & (global_df["sub-metric"] == submetric)]
        quarters = set(local_df.loc[local_df["year"] == endYear]["quarter"].unique()) if startYear != endYear else set([q for q in [1, 2, 3, 4] if q >= startQuarter])
        for p in predictors:
            quarters = quarters.intersection(set(revenue_df.loc[(revenue_df["company"] == p) & (revenue_df["year"] == endYear)]["quarter"]))
        return sorted(list(quarters))
    return [1, 2, 3, 4]

'''Generates 2 regression plots: predicted vs. actual revenue growth, linear coefficients for each predictor'''
@app.callback(
    Output("regression-graph1", "figure"),
    Output("regression-graph2", "figure"),
    Output("regression-graph-block","style"),
    Output("regression-table-block","style"),
    Input("regression-comp-dropdown","value"),
    Input("regression-segment-dropdown","value"),
    Input("regression-ticker-dropdown", "value"),
    Input("regression-start-dropdown","value"),
    Input("regression-startq-dropdown","value"),
    Input("regression-end-dropdown","value"),
    Input("regression-endq-dropdown","value"),
    Input("btn-regress","n_clicks"),
    prevent_initial_call=True
)
def make_regression_graph(company, submetric, predictors, startYear, startQuarter, endYear, endQuarter, btn):
    changed_id = [p['prop_id'] for p in callback_context.triggered][0]
    if 'btn-regress' in changed_id:
        y_company, x_customers = regressions.preprocess(startYear, startQuarter, endYear, endQuarter, submetric, company, predictors)
        r_sq, predicted, coefficients, model_linear, reg, prediction_fig, coeff_fig = regressions.regression(y_company, x_customers, company, predictors, submetric, startYear, startQuarter, endYear, endQuarter)
        return prediction_fig, coeff_fig, {"display":"inline-block"}, {"display":"inline-block"}
    return go.Figure(), go.Figure(), {"display":"none"}, {"display":"none"}

'''Displays regression tab help button'''
@app.callback(
    Output("modal-regression", "is_open"),
    [Input("open-regression", "n_clicks"), Input("close-regression", "n_clicks")],
    [State("modal-regression", "is_open")],
)
def toggle_modal_regression(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

'''Formats quarter and year into quarter-string for x-axis labels on visualizations'''
def join_quarter_year(quarter, year):
    return str(year)[-2:]+ "Q" + str(quarter)

if __name__ == "__main__":
    app.run_server(debug=True)

