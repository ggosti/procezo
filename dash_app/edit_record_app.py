import json
import numpy as np
import pandas as pd

from dash import Dash, html, dcc, Output, Input, State
import dash

import numpy as np
import pandas as pd
import json

from dash_app.callbacks import register_callbacks_vars,register_callbacks_records


import requests




def remove_record(n_clicks,data):
    print('n_clicks',n_clicks)
    if n_clicks>0:
        print("Remove ",data)
        dff = json.loads(data) #= pd.read_json(data)
        project_name = dff['project_name']
        group_name = dff['group_name']
        record_name = dff['record_name']
        print('dff',dff)
        if record_name is not None:
            version='preprocessed-VR-sessions'
            requests.delete(f"{FASTAPI_URL}/record/proc/{project_name}/{group_name}/{record_name}/{version}")
            # record = projObj.get_record(project_name,group_name,record_name+'-preprocessed','proc',version='preprocessed-VR-sessions')
            # projObj.remove_record(record)
            # procRecord = projObj.get_record(project_name,group_name,record_name+'-preprocessed','proc',version='preprocessed-VR-sessions')
            # print('procRecord',procRecord)
            # if procRecord is not None:
            #    procGroup = procRecord.group
            #    print('keys',procGroup.pars['preprocessedVRsessions'].keys())
            #    print('remove name',procRecord.name)
            #    del procGroup.pars['preprocessedVRsessions'][procRecord.name]
            #    print('keys',procGroup.pars['preprocessedVRsessions'].keys())
            #    procGroup.updateParFile()
            #    os.remove(procRecord.path)
            #    utils.records.remove(procRecord)
    return [0.0, 3600.0]


#def init_callbacks(app):




dash_app = dash.Dash(__name__, requests_pathname_prefix='/edit_record/') #,  external_stylesheets=[dbc.themes.BOOTSTRAP]  )


layout1 = html.Div(
        [
            html.H1(children="Edit Record", style={"textAlign": "center"}),
            html.P(children="Select Roi in sessions from immersive and not-immersive explorations of Aton 3D " 
                              + "models which were captured with Merkhet. "),
            #dcc.Location(id='url2', refresh=False),
            html.P(id='record-vars'), #dcc.Store(id='variables')
            html.P(id="preprocessed-record-name", children= "Preprocessed record is stored at startup: < None >"),
            html.P(children="Saved Range x-axis"),
            html.P(id="x-slider-endpoints",children= json.dumps({'values' : [None,None],'min':0.,'max':3600.} ) ),  #str([0., 3600.])),
            dcc.Graph(id="record-plot",style={'height': '60vh'}),
            dcc.RangeSlider(
                id='x-slider',
                min=0, max=3600., step=1.,
                marks={0: '0', 3600.: '3600'},
                value=[0., 3600.]
                ),
            html.P(children="New Range x-axis"),
            html.P(id="x-slider-proc-endpoints",children=str([None,None])),
            html.P(id="proc-folder",children="Save in: preprocessed-VR-sessions"), # In futire to change folder name html.Div(dcc.Input(id='input-on-submit', type='text')),
            html.Button('Save', id='save-val', n_clicks=0),
            html.Button('Remove', id='remove-rec', n_clicks=0),
            html.Div(id='container-button-basic',
                children='Enter a roi and save it'),
            html.Div(id='container-button-remove',
                children=''),
            dcc.Graph(id="3d-record-plot"),
            # dcc.Store stores record variable: project_name, group_name, record_name
            dcc.Store(id='record-variables')
            
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
register_callbacks_records(dash_app) #init_callbacks(dash_app)

        
#if __name__ == "__main__":
#    dash_app.run_server(debug=True, port=8050)