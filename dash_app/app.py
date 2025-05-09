import dash

from dash import dcc, html, Input, Output, State
import requests
import pandas as pd
import plotly.express as px

#from dash_app.layout import layout
from dash_app.callbacks import register_callbacks

FASTAPI_URL = "http://localhost:8000/api"

dash_app = dash.Dash(__name__, requests_pathname_prefix='/dashboard/')
dash_app.title = "Record Dash"
# dash_app.layout = layout

register_callbacks(dash_app)


# App layout
dash_app.layout = html.Div([
    html.H2("Time Series Viewer"),
    dcc.Dropdown(id="project-dropdown", placeholder="Select a project"),
    dcc.Dropdown(id="group-dropdown", placeholder="Select a group"),
    dcc.Dropdown(id="file-dropdown", placeholder="Select a CSV file"),
    dcc.Graph(id="timeseries-graph")
])


