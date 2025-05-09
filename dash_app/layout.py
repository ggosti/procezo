from dash import dcc, html

layout = html.Div([
    html.H2("Time Series Viewer"),
    dcc.Dropdown(id="project-dropdown", placeholder="Select a project"),
    dcc.Dropdown(id="group-dropdown", placeholder="Select a group"),
    dcc.Dropdown(id="file-dropdown", placeholder="Select a CSV file"),
    dcc.Graph(id="timeseries-graph")
])