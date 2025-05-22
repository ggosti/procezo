import os
import json
import numpy as np
import pandas as pd

from dash import Dash, html, dcc
import dash
#from flask import g

from dash_app.callbacks import register_callbacks_vars , register_callbacks_group


dash_app = dash.Dash(__name__, requests_pathname_prefix='/edit_group/') #,  external_stylesheets=[dbc.themes.BOOTSTRAP]  )

layout1 = html.Div(
        [
            html.H1(children="Group Proc.", style={"textAlign": "center"}),
            html.P(children="Gate records in a group from immersive and not-immersive explorations of Aton 3D " 
                              + "models which were captured with Merkhet. "
                              + "Records in a group are gated according to time duration and variance."),
            html.P(id='group-vars'), #dcc.Store(id='variables')
            dcc.Checklist(["Panoramic"], [], id="panoramic-checklist", inline=True),
            html.P(id="panoramic-checklist-dialog" ,children= ""),
            html.P(children= "Preprocessed records pre-gate:"),
            html.P(id="preprocessed-record-names", children= "< None >"),
            dcc.Graph(id="scatter-plot"),
            html.P(children="Gate range x-axis"),
            html.P(id="x-slider-output",children=str([0., 360.])),
            dcc.RangeSlider(
                    id='x-slider-2',
                    min=0, max=360., #step=1.,
                    marks={0: '0', 360.: '360'},
                    value=[0., 360.]
                    ),
            html.P(children="Gate range y-axis"),
            html.P(id="y-slider-output",children=str([0., 2.])),
            dcc.RangeSlider(
                    id='y-slider',
                    min=0, max=2., #step=0.01,
                    marks={0: '0', 2.: '2.'},
                    value=[0., 2.]
                    ),
            html.P(children= "Saved preprocessed records post-gate:"),
            html.P(id="preprocessed-gated-record-names", children= "< None >"),
            html.P(children= "Selected preprocessed records post-gate:"),
            html.P(id="preprocessed-gated-selected-record-names", children= "< None >"),
            html.Button('Save selected records', id='save-gate', n_clicks=0),
            html.P(id="button-basic-responce", children= "not saved"),
            dcc.Store(id='group-variables'),
        ])


project_name = '<None>'
group_name = '<None>'
record_name = '<None>'

dash_app.layout =  html.Div([
        # represents the browser address bar and doesn't render anything
        dcc.Location(id='url', refresh=False),
        html.A(id="logout-link", children="Main page", href="/"),
        html.Div(id='project-name', children = f"Project: {project_name}"),
        #html.P(children="Project:"),
        #dcc.Input(id="project-input1", type="text", placeholder=project_name),
        html.Div(id='group-name', children = f"Group: {group_name}"),
        html.Div(id='record-name', children = f"Record: {record_name}"),
        layout1, #html.Div(id='page-content'),
        dcc.Store(id='variables'),
])


register_callbacks_vars(dash_app)
register_callbacks_group(dash_app)

if __name__ == "__main__":
    dash_app.run_server(debug=True, port=8050)

