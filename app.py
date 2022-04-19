from logging import Filterer
from dash import Dash, html, dcc, Input, Output, callback_context, dash_table
import plotly.express as px
import pandas as pd
import numpy as np
import statsmodels.api as sm
import plotly.graph_objs as go
import dash_bootstrap_components as dbc
from datetime import datetime
import scraper, stocks, json, pickle

pd.options.mode.chained_assignment = None
app = Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])

# Pull JSON files
global_df = pd.read_json("data/data.json")
umc = pd.read_json("data/umc_json_data.json")
smic = pd.read_json("data/smic_json_data.json")
gf = pd.read_json("data/gf_json_data.json")

# Global dictionaries and variables
metric_to_var = {"Revenue by Technology": "rev_tech", "Revenue by Segment": "rev_seg", "Revenue by Geography": "rev_geo", "CapEx": "capex", "Inventory": "inv", "Revenue":"rev"}
var_to_metric = {v:k for k, v in metric_to_var.items()}
tsmc_subs = global_df.loc[global_df["company"] == "TSMC"]["sub-metric"].unique().tolist()
company_df = {"SMIC": smic, "UMC": umc, "Global Foundries": gf}
company_abbrev = {"SMIC": "smic", "UMC": "umc", "Global Foundries": "gf", "TSMC":"tsmc"}
firstYear = 2000
currYear = datetime.now().year

# Read ticker options
with open("tickers.txt", "rb") as f:
    ticker_options = pickle.load(f)

controls = html.Div(
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
            className="mb-3", style={'width': '48%', 'float': 'left', 'display': 'inline-block', 'margin': '10'}
        ),

        html.Div(
            [
                html.Button("Download Data", id= "btn-data"),
                dcc.Download(id="download-data-csv"),
                dcc.Store(id="dataframe", data=[]),
                dcc.Store(id="json-store", data=[])
                
            ]
        ),
    ],
    #style={'verticalAlign': 'top', 'margin-top':0}
    #body=True,
)

parsing = html.Div(
    [
    dbc.Card(
    [
        html.Div(
            [
                dbc.Label("URL"),
                dcc.Input(
                    id="url-input".format("url"),
                    type="url",
                    placeholder="Enter URL to Parse".format("url"),
                    style={"margin-left": 10}
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
                dcc.Input(
                    id="year-input".format("number"),
                    type="number",
                    placeholder="Enter Year".format("number"),
                    style={"margin-left": 10, "margin-top":10}
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
                html.Button("Scrape PDF", id= "btn-scrape", style={"margin-top": 10}, n_clicks=0),   
            ]
        ),
    ],
    body=True,
    ),
    dbc.Card(
    [
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
                dcc.Input(
                    id="manual-year-input".format("number"),
                    type="number",
                    placeholder="Enter Year".format("number"),
                    style={"margin-left": 10, "margin-top":10}
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
                html.Button("Manual Input", id= "btn-manual", style={"margin-top": 10}, n_clicks=0),   
            ]
        )
    ],
    body=True,
    )
    ]
)

puller = dbc.Card(
    [
        html.Div([
            dbc.Label("Custom Ticker"),
            dcc.Input(
                    id="input-ticker",
                    style={"margin-left": 10}
                ),
        ],
        ),

        html.Div([
            html.Button("Add Ticker", id= "btn-add-ticker", style={"margin-top": 10, "margin-right": 10, "margin-bottom": 10}, n_clicks=0),
            html.Button("Remove Ticker", id= "btn-remove-ticker", style={"margin-top": 10, "margin-bottom": 10}, n_clicks=0),
        ]
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
            [
                html.Button("Update Selected Tickers", id= "btn-pull", style={"margin-top": 10, "margin-right": 10}, n_clicks=0),
                html.Button("Update All Tickers", id= "btn-update-all", style={"margin-top": 10}, n_clicks=0),   
   
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

buttons = html.Div(
    [
        html.Div(
            [
            html.Button("Approve", id= "btn-approve", style={"margin-right": 10, "display":"none"}, n_clicks=0),   
            html.Button("Reject", id= "btn-reject", style={"margin-right": 10, "display":"none"}, n_clicks=0),
            html.Button("Undo", id= "btn-undo", style={"margin-right": 10, "display":"none"}, n_clicks=0)
            ]   
        ),
        html.Div(
            id='confirmation-msg',
            children='Press "Approve" to confirm that the scraped data is accurate.',
            style={"display":"none"}
        ),    
    ],
)

app.layout = html.Div([
    dcc.Tabs([
        dcc.Tab(label="Visualization", children=[
        dbc.Container(
            [
                html.H1("Intel Competitor Visualizations", style={'width': '48%', 'display': 'inline-block', 'margin': 20}),
                html.Hr(),
                dbc.Row(
                    [
                        dbc.Col(controls, md=4, style={"position":"top"}),
                        dbc.Col([
                            dcc.Graph(id="graph"),
                            dash_table.DataTable(
                                data=[],
                                id="df-viz",
                                style_table={
                                    'height': 400,
                                    'overflowY': 'scroll'
                                }
                                )],
                            md=8),
                    ],
                    align="center",
                ),
            ],
            fluid=True,
        )
        ]),
        dcc.Tab(label="Scraping", children=[
        dbc.Container(
            [
                html.H1("Intel Competitor Parsing", style={'width': '48%', 'display': 'inline-block', 'margin': 20}),
                html.Hr(),
                dbc.Row(
                    [
                        dbc.Col(parsing, md=4),
                        dbc.Col(
                            [
                                dash_table.DataTable(data=[], id="df-scraped"),
                                dash_table.DataTable(
                                    id = 'manual-dt',
                                    columns=(
                                        [{'id': 'capex','name':'Capex'}]+
                                        [{'id': 'inventory','name':'Inventory'}]
                                    ),
                                    data=[
                                        {'column-{}'.format(i): (j + (i-1)*2) for i in range(1, 2)}
                                        for j in range(1)
                                    ],
                                    editable=True
                                ),
                                dash_table.DataTable(
                                    id = 'seg-submetrics-dt',
                                    columns=(
                                        [{'id': 'rev-seg','name':'Revenue by Segment Submetric'}]+
                                        [{'id': 'rev-seg-value','name':'Value'}]
                                    ),
                                    data=[
                                        {'column-{}'.format(i): (j + (i-1)*5) for i in range(1, 5)}
                                        for j in range(5)
                                    ],
                                    editable=True,
                                    row_deletable=True
                                ),
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
        dcc.Tab(label="Pulling", children=[
            dbc.Container([
                html.H1("Revenue Extraction", style={'width': '48%', 'display': 'inline-block', 'margin': 20}),
                html.Hr(),
                dbc.Row(
                    [
                        dbc.Col(puller, md=4),
                        dbc.Col(
                            [dash_table.DataTable(data=[], id="df-pulled")
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

@app.callback(
    Output("metric-dropdown","options"),
    Input("company-dropdown", "value")
)
def setMetric(company):
    if company:
        local_df = global_df
        local_df = local_df.loc[(local_df["company"] == company)]
        metrics = local_df["metric"].dropna().unique()
        metrics = [var_to_metric[m] for m in metrics]
        return metrics
    return ["Revenue by Technology", "Revenue by Segment", "Revenue by Geography", "CapEx", "Inventory"]

#viz call back options
@app.callback(
    Output("viz-dropdown","options"),
    Output("viz-dropdown","value"),
    Input("metric-dropdown","value")
)
def visualization_options(metric):
    if metric != "CapEx" and metric != "Inventory" and metric != "Revenue" and metric != None:
        return ["Comparison","Individual"],"Comparison"
    else:
        return [],None

#submetric call back
@app.callback(
    Output("submetric-dropdown","options"),
    Input("company-dropdown","value"),
    Input("metric-dropdown","value"),
    Input("viz-dropdown","value")
)
def set_submetric(company,metric,viz):
    if viz == "Comparison" or viz == None:
        return []
    else:
        local_df = global_df
        local_df = local_df.loc[(local_df["company"] == company) & (local_df["metric"] == metric_to_var[metric])]
        return local_df["sub-metric"].dropna().unique()

@app.callback(
    Output("start-dropdown","options"),
    Input("company-dropdown","value"),
    Input("metric-dropdown","value"),
    Input("submetric-dropdown", "value"),
)
def setStartYear(company,metric,submetric):
    if all([company, metric]):
        local_df = global_df
        local_df = local_df.loc[(local_df["company"] == company) & (local_df["metric"] == metric_to_var[metric])]
        if submetric:
            local_df = local_df.loc[(local_df["sub-metric"] == submetric)]
        years = local_df["year"].dropna().unique()
        return years
    return np.arange(firstYear, currYear)

@app.callback(
    Output("startq-dropdown","options"),
    Input("company-dropdown","value"),
    Input("metric-dropdown","value"),
    Input("submetric-dropdown", "value"),
    Input("start-dropdown","value")
)
def setStartQuarter(company,metric,submetric, startYear):
    if all([company, metric, startYear]):
        local_df = global_df
        local_df = local_df.loc[(local_df["company"] == company) & (local_df["metric"] == metric_to_var[metric]) & (local_df["year"] == startYear)]
        if submetric:
            local_df = local_df.loc[(local_df["sub-metric"] == submetric)]
        quarters = local_df["quarter"].dropna().unique()
        return quarters
    return [1, 2, 3, 4]

@app.callback(
    Output("end-dropdown","options"),
    Input("company-dropdown","value"),
    Input("metric-dropdown","value"),
    Input("submetric-dropdown", "value"),
    Input("start-dropdown", "value"),
)
def setEndYear(company,metric,submetric,startYear):
    if all([company, metric, startYear]):
        local_df = global_df
        local_df = local_df.loc[(local_df["company"] == company) & (local_df["metric"] == metric_to_var[metric])]
        if submetric:
            local_df = local_df.loc[(local_df["sub-metric"] == submetric)]
        years = local_df.loc[(local_df["year"]) >= startYear]["year"].dropna().unique()
        return years
    return np.arange(firstYear, currYear)

@app.callback(
    Output("endq-dropdown","options"),
    Input("company-dropdown","value"),
    Input("metric-dropdown","value"),
    Input("submetric-dropdown", "value"),
    Input("start-dropdown", "value"),
    Input("startq-dropdown", "value"),
    Input("end-dropdown", "value"),
)
def setEndQuarter(company,metric,submetric,startYear,startQuarter,endYear):
    if all([company, metric, startYear, startQuarter, endYear]):
        local_df = global_df
        local_df = local_df.loc[(local_df["company"] == company) & (local_df["metric"] == metric_to_var[metric])]
        if submetric:
            local_df = local_df.loc[(local_df["sub-metric"] == submetric)]
        quarters = local_df.loc[local_df["year"] == endYear]["quarter"].dropna().unique()
        if startYear == endYear:
            quarters = [q for q in quarters if q >= startQuarter]
        return quarters
    return [1, 2, 3, 4]

#graph call back
@app.callback(
    Output("graph", "figure"),
    Output("dataframe","data"),
    Output("df-viz", "data"),
    Output("df-viz", "columns"),
    [
        Input("company-dropdown", "value"),
        Input("metric-dropdown", "value"),
        Input("viz-dropdown", "value"),
        Input("submetric-dropdown", "value"),
        Input("start-dropdown", "value"),
        Input("startq-dropdown", "value"),
        Input("end-dropdown", "value"),
        Input("endq-dropdown", "value"),
    ],
    prevent_initial_call=True,
)
def make_graph(company, metric, viz, submetric, start_year, start_quarter, end_year, end_quarter):
    if metric == "CapEx" or metric == "Inventory":
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
        return graph, {}

    local_df = global_df
    local_df = local_df.loc[(local_df["company"] == company) & (local_df["metric"] == metric_to_var[metric])]
    if (submetric != None or submetric != "NaN") and viz == "Individual":
        local_df = local_df.loc[local_df["sub-metric"] == submetric]
    local_df["quarter-string"] = local_df["year"].map(lambda x: str(x)[-2:]) + "Q" + local_df["quarter"].map(str)
    local_df = local_df.sort_values(by=["quarter-string"])
    start_q = join_quarter_year(start_quarter, start_year)
    end_q = join_quarter_year(end_quarter, end_year)

    try:  
        index_start = local_df["quarter-string"].tolist().index(start_q)
        index_end = len(local_df["quarter-string"].tolist()) - local_df["quarter-string"].tolist()[::-1].index(end_q) - 1
    except ValueError:
        return graph, {}

    filtered_data = local_df.iloc[index_start:index_end + 1]
    filtered_data.loc[:,("value")] = filtered_data["value"].astype(float)
    
    if viz == "Comparison":
        graph = px.bar(filtered_data, x="quarter-string", y="value",
        color="sub-metric",
        labels={
                "quarter-string": "Quarters",
                "value": "Percentage %",
                "sub-metric": f'{metric.split()[-1]}'
            },
        title=f'{metric} for {company} from {start_q} to {end_q}')
    elif submetric == None or submetric == "NaN":
        graph = px.line(filtered_data, x="quarter-string", y="value",
        labels={
        "quarter-string": "Quarters",
        "value": "US$ Dollars (Millions)",
            },
        title=f'{metric} for {company} from {start_q} to {end_q}', markers=True)
    else:
        graph = px.line(filtered_data, x="quarter-string", y="value",
        labels={
        "quarter-string": "Quarters",
        "value": "US$ Dollars (Millions)",
            },
        title=f'{metric}: {submetric} for {company} from {start_q} to {end_q}', markers=True)
    return graph,filtered_data.to_dict(), filtered_data.to_dict('records'), [{"name": i, "id": i} for i in filtered_data.columns]

# Download data callback
@app.callback(
    Output("download-data-csv","data"),
    Input("btn-data","n_clicks"),
    Input("dataframe","data"),
    prevent_initial_call=True,
)
def export_graph(n_clicks,dataframe):
    changed_id = [p['prop_id'] for p in callback_context.triggered][0]
    if 'btn-data' in changed_id:
        return dcc.send_data_frame(pd.DataFrame(dataframe).to_csv, "data_analysis.csv")
    return None

# Scrape PDF callback
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

# @app.callback(
#     Output("btn-approve","style"),
#     Output("btn-reject","style"),
#     Output("btn-undo","style"),
#     Output("confirmation-msg","style"),
#     Output("manual-dt","style"),
#     Output("seg-submetrics-dt","style"),
#     Output("seg-submetrics-dt","data"),
#     Input("manual-company-input","value"),
#     Input("manual-year-input","value"),
#     Input("manual-quarter-input","value"),
#     Input("btn-manual"),
#     prevent_initial_call=True
# )

# Gets called when user clicks 'Approve' or 'Reject'
@app.callback(
    #Output("btn-approve","style"),
    #Output("btn-reject","style"),
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
        with open("data/data.json") as json_data:
            old_data = json.load(json_data)
            json_data.close()
        if json_store[-1] in old_data:
            return "Data already exists in the global dataset."
        else:
            old_data.extend(json_store)
            with open("data/data.json","w") as json_file:
                json.dump(old_data,json_file,indent=4,separators=(',',': '))
                json_file.close()
            return f'{company} {quarter_year} has been added to the global dataset.'
    elif 'btn-undo' in changed_id:
        with open("data/data.json") as current_json:
            current = json.load(current_json)
            current_json.close()
        if json_store[-1] in current:
            current = current[:-(len(json_store))]
            with open("data/data.json","w") as json_file:
                json.dump(current,json_file,indent=4,separators=(',',': '))
                json_file.close()
            return "Data been removed from global dataset."
        else:
            return "There is nothing left to undo."
    return ""

@app.callback(
    Output("ticker-dropdown", "options"),
    Input("input-ticker", "value"),
    Input("btn-add-ticker", "n_clicks"),
    Input("btn-remove-ticker", "n_clicks"),
    Input("ticker-dropdown", "options"),
    prevent_initial_call=True,
)
def change_tickers(new_ticker, btnAdd, btnRemove, tickers):
    changed_id = [p['prop_id'] for p in callback_context.triggered][0]
    if 'btn-add-ticker' in changed_id:
        new_ticker = new_ticker.upper()
        if new_ticker not in tickers:
            tickers.append(new_ticker)
            with open("tickers.txt", "wb") as f:
                pickle.dump(tickers, f)
    elif 'btn-remove-ticker' in changed_id:
        try:
            tickers.remove(new_ticker)
        except:
            'Placeholder'
        with open("tickers.txt", "wb") as f:
            pickle.dump(tickers, f)
    return tickers

@app.callback(
    Output("df-pulled", "data"),
    Output("df-pulled", "columns"),
    Input("ticker-dropdown", "value"),
    Input("ticker-dropdown", "options"),
    Input("btn-pull", "n_clicks"),
    Input("btn-update-all", "n_clicks"),
    prevent_initial_call=True,
)
def pull_revenue(tickerVal, tickerOptions, btnPull, btnUpdate):
    if btnPull + btnUpdate > 0:
        changed_id = [p['prop_id'] for p in callback_context.triggered][0]
        tickers = []
        if 'btn-pull' in changed_id:
            tickers = tickerVal
        elif 'btn-update-all' in changed_id:
            tickers = tickerOptions
        old_df = pd.read_csv("data/revenue.csv")
        old_cols = old_df.columns
        #Pull tickers that haven't been updated yet, FIXME: Check more rigorously
        filtered_tickers = [t for t in tickers if (f'{t.lower()}_revenue' not in old_cols or not old_df.iloc[-1,:][f'{t.lower()}_revenue'])]
        if filtered_tickers:
            new_df = stocks.get_revenue_list(filtered_tickers).replace({"":np.nan, "None":0.0})
            new_cols = new_df.columns
            combine_cols = [col for col in set(old_cols.append(new_cols)) if col in old_cols and col in new_cols]
            combined = pd.merge(old_df, new_df, how='outer', on=combine_cols).fillna(0.0) if (not old_df.empty) else new_df
            combined = combined.drop_duplicates().groupby(["year", "quarter", "reportedCurrency"], as_index=False).max()
            #print(combined)
            combined.to_csv("data/revenue.csv", index=False)
            return new_df.to_dict('records'), [{"name": i, "id": i} for i in new_df.columns]
        recent_cols = ["year","quarter","reportedCurrency"] + [f'{t.lower()}_revenue' for t in tickers]
        recent_df = old_df[recent_cols]
        return recent_df.to_dict('records'), [{"name": i, "id": i} for i in recent_df.columns]
    return [],[]

def join_quarter_year(quarter, year):
    return str(year)[-2:]+ "Q" + str(quarter)

if __name__ == "__main__":
    app.run_server(debug=True)

