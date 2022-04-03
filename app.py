from logging import Filterer
from re import sub
import dash
from dash import Dash, html, dcc, Input, Output
import plotly.express as px
import pandas as pd
import numpy as np
import statsmodels.api as sm
import plotly.graph_objs as go
import dash_bootstrap_components as dbc
pd.options.mode.chained_assignment = None

app = Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])
global_df = pd.read_json("json_data.json")
umc = pd.read_json("umc_json_data.json")
smic = pd.read_json("smic_json_data.json")
gf = pd.read_json("gf_json_data.json")
metric_dict = {"Revenue by Technology": "rev_tech", "Revenue by Segment": "rev_seg", "Revenue by Geography": "rev_geo", "CapEx": "capex", "Inventory": "inv"}
tsmc_subs = global_df.loc[global_df["company"] == "TSMC"]["sub-metric"].unique().tolist()


company_df = {"SMIC": smic, "UMC": umc, "Global Foundries": gf}

#Dummy TSMC DataFrame
tsmc_rev = np.array([4496, 5796.7, 7250.1, 9186.5, 9520.5, 11336.4, 11522.9, 11898.9, 10562.6, 14984, 15253.4, 18098.7, 21323.1, 27244.1, 30126, 33856.1, 4910.1, 36839.7, 38215.1,47832.2])
tsmc_net_income = np.array([517.3, 771.8, 1687.9, 3297.1, 3342.1, 4536.2, 3899.3, 3569.2, 3186.5, 5771.8, 4793.1, 695.9, 6570.9, 9082.5, 10816.5, 11847.3, 12321.8, 12540.8, 12331.3, 18496.6])
tsmc_years = np.arange(2001,2021)
tsmc = pd.DataFrame({"Quarters":tsmc_years, "Revenue": tsmc_rev, "Net Income": tsmc_net_income})

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
                    #options = global_df["sub-metric"].dropna().unique(),
                    #options = ["Smartphone", "Internet of Things", "High Performance Computing", "Automotive", "Digital Consumer Electronics", "Others"],
                    value=""
                ),
                
            ]
        ),

        html.Div(
            [
                dbc.Label("Starting Year", html_for="start-dropdown"),
                dcc.Dropdown(
                    options= np.arange(2001, 2021),
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
                    options= np.arange(2001, 2021),
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

        # html.Div(
        #     [
        #         html.Button("Download Graph", id= "btn-graph"),
        #         dcc.Download(id="download-graph-png"),
                
        #     ]
        # ),
    ],
    body=True,
)

parsing = dbc.Card(
    [
        html.Div(
            [
                dbc.Label("URL"),
                dcc.Input(
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
                dcc.Input(
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
                    options=["1","2","3","4"]
                ),
            ],
        ),
    ],
    body=True,
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
                        dbc.Col(controls, md=4),
                        dbc.Col(dcc.Graph(id="graph"), md=8),
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
                    ],
                    align="center",
                ),
            ],
            fluid=True,
        )
        ]),
    ])
])

#viz call back options
@app.callback(
    Output("viz-dropdown","options"),
    Output("viz-dropdown","value"),
    Input("metric-dropdown","value")
)
def visualization_options(metric):
    if metric != "CapEx" and metric != "Inventory" and metric != None:
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
        local_df = company_df[company] if company != "TSMC" else global_df
        local_df = local_df.loc[(local_df["company"] == company) & (local_df["metric"] == metric_dict[metric])]
        return local_df["sub-metric"].dropna().unique()

#graph call back
@app.callback(
    Output("graph", "figure"),
    [
        Input("company-dropdown", "value"),
        Input("metric-dropdown", "value"),
        Input("viz-dropdown", "value"),
        Input("submetric-dropdown", "value"),
        Input("start-dropdown", "value"),
        Input("startq-dropdown", "value"),
        Input("end-dropdown", "value"),
        Input("endq-dropdown", "value")
    ],
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
                "text": "Data does not exist for selected time span. Choose different range",
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
        return graph

    local_df = company_df[company] if company != "TSMC" else global_df
    local_df = local_df.loc[(local_df["company"] == company) & (local_df["metric"] == metric_dict[metric])]
    if (submetric != None or submetric != "NaN") and viz == "Individual":
        local_df = local_df.loc[local_df["sub-metric"] == submetric]
    local_df = local_df.sort_values(by=["quarter"])
    #print(local_df)
    print(submetric)
    print(local_df)
    start_q = (start_quarter + "Q" + str(start_year)[-2:]) if company == "TSMC" else (str(start_year)[-2:] + "Q" + start_quarter)
    end_q = (end_quarter + "Q" + str(end_year)[-2:]) if company == "TSMC" else (str(end_year)[-2:] + "Q" + end_quarter)

    try:  
        index_start = local_df["quarter"].tolist().index(start_q)
        index_end = len(local_df["quarter"].tolist()) - local_df["quarter"].tolist()[::-1].index(end_q) - 1
    except ValueError:
        return graph

    filtered_data = local_df.iloc[index_start:index_end + 1]
    print(filtered_data)
    #parse data for $ or %
    if "$" in str(filtered_data.iloc[0,filtered_data.columns.get_loc('value')]):
        cleaned_column = filtered_data["value"].str[1:].astype(float)
    else:
        cleaned_column = filtered_data["value"].str[:-1].astype(float) / 100
        
    filtered_data.loc[:,("value")] = cleaned_column
    
    if viz == "Comparison":
        graph = px.bar(filtered_data, x="quarter", y="value",
        color="sub-metric",
        labels={
                "quarter": "Quarters",
                "value": "Percentage %",
            },
        title=f'{metric} for {company}')
    elif submetric == None or submetric == "NaN":
        graph = px.line(filtered_data, x="quarter", y="value",
        labels={
        "quarter": "Quarters",
        "value": "US$ Dollars (Millions)",
            },
        title=f'{metric} for {company}', markers=True)
    else:
        graph = px.line(filtered_data, x="quarter", y="value",
        labels={
        "quarter": "Quarters",
        "value": "US$ Dollars (Millions)",
            },
        title=f'{metric}: {submetric} for {company}', markers=True)
    #scatter_plot = px.scatter(filtered_data, x="Quarters", y=y, title=f'{y} for TSMC', markers=True, trendline="ols")
    #results = px.get_trendline_results(line)
    return graph

# @app.callback(
#     Output("download-graph-png","data"),
#     Input("btn-graph","n_clicks"),
#     Input("graph","figure"),
#     prevent_initial_call=True,
# )
# def export_graph(n_clicks,graph):
#     graph = dcc.Graph(figure=graph)
#     return dcc.send_bytes(graph,"data_vis")

if __name__ == "__main__":
    app.run_server(debug=True)

