from dash import dcc, html

layout = html.Div([
    html.H2("Time Series Viewer"),
    dcc.Dropdown(id="project-dropdown", placeholder="Select a project"),
    dcc.Dropdown(id="group-dropdown", placeholder="Select a group"),
    dcc.Dropdown(id="file-dropdown", placeholder="Select a CSV file"),
    dcc.Graph(id="timeseries-graph")
])

project_name = '<None>'
group_name = '<None>'
record_name = '<None>'

layout_vars_app = html.Div([
        # represents the browser address bar and doesn't render anything
        dcc.Location(id='url', refresh=False),
        html.A(id="logout-link", children="Main page", href="/"),
        html.Div(id='project-name', children = f"Project: {project_name}"),
        #html.P(children="Project:"),
        #dcc.Input(id="project-input1", type="text", placeholder=project_name),
        html.Div(id='group-name', children = f"Group: {group_name}"),
        html.Div(id='record-name', children = f"Record: {record_name}"),
        html.Div(id='page-content'),
        dcc.Store(id='variables'),
])