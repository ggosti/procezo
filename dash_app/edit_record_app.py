import json
import numpy as np
import pandas as pd

from dash import Dash, html, dcc, Output, Input, State
import dash

import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go

import numpy as np
import pandas as pd
import json

from dash_app.callbacks import register_callbacks_vars 

import timeSeriesInsightToolkit as tsi


import requests

FASTAPI_URL = "http://localhost:8000/api"

def get_record(step,project_name,group_name,record_name):    
    url = f"{FASTAPI_URL}/record/{step}/{project_name}/{group_name}/{record_name}"
    # Make the GET request
    response = requests.get(url)

    # Raise error if something went wrong
    response.raise_for_status()

    # Convert JSON response to DataFrame
    data = response.json()

    return data

def get_record_df(step,project_name,group_name,record_name):
    data = get_record(step,project_name,group_name,record_name)
    df = pd.DataFrame(data["rows"])
    timekey = data["timeKey"]
    pars = data["pars"]
    return df, timekey, pars


def make_plot(df, t,plotLines,lineName,n,navAr,x_filter):  
    if 'fx' in lineName:
        obsNum = 3
    else:
        obsNum = 2
    rh = [0.3] +  [0.1]*obsNum +[0.1]*obsNum + [0.1]
    n_rows = 1+obsNum+obsNum+1
    fig = make_subplots(
        rows=n_rows, cols=1,
        #shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights = rh,
        specs= [[{"type": "table"}]] + [[{"type": "scatter"}]] * obsNum + [[{"type": "scatter"}]] * obsNum + [[{"type": "scatter"}]],
        subplot_titles=["Talbe"]  + ["Crop"] * obsNum  +  ["Raw" ] * obsNum + ["Raw Nav" ]
    )

    #print('t',t)
    #print('navAr',navAr)
    #print('navVr',n)

    #print('min l',plotLines, np.nanmin(plotLines))
    fig.add_trace(
        go.Scatter(
            x=t,
            y= navAr, #np.nanmin(plotLines)*navAr,
            mode='lines',
            name="AR",
            #fill= "toself", 
        ),
        row=n_rows, col=1
    )

    # fig.add_trace(
    #     go.Scatter(
    #         x=t,
    #         y=+np.nanmax(plotLines)*navAr,
    #         mode='none',
    #         name="AR Raw",
    #         fill="tonexty",  # fill area between trace0 and trace1
    #     ),
    #     row=n_rows, col=1
    # )

    # swhow VR and AR
    fig.add_trace(
        go.Scatter(
            x=t,
            y= n,
            mode='lines',
            name="VR",
            #fill= "toself", 
        ),
        row=n_rows, col=1
    )
    fig.update_yaxes(title_text="mode", row=n_rows, col=1)
    fig.update_xaxes(title_text="time", row=n_rows, col=1)

    # fig.add_trace(
    #     go.Scatter(
    #         x=t,
    #         y=+np.nanmax(plotLines)*n,
    #         mode='none',
    #         name="VR Raw",
    #         fill="tonexty",  # fill area between trace0 and trace1
    #     ),
    #     row=n_rows, col=1
    # )

    goToRows = [ i  for i in range(obsNum) for j in range(3)]
    #print('goToRows',goToRows)
    # Add raw data
    for r, l,ln in zip(goToRows, plotLines,lineName):
        print(ln,l.mean())
        #print(l)
        fig.add_trace(
            go.Scatter(
                x=t,
                y=l-np.nanmean(l),
                mode="lines",
                name=ln+" Raw"
            ),
            row=n_rows-r-1, col=1
        )
        fig.update_yaxes(title_text=ln[:-1] + "- <"+ln[:-1] +">" , row=n_rows-r-1, col=1)

  

    # Add proc data
    for i in range(obsNum):
        fig.add_vrect( x0=x_filter[0], x1=x_filter[1], row=n_rows-i-1, col=1)
    
    for r, l,ln in zip(goToRows, plotLines,lineName):
        ltemp = l[(t>=x_filter[0]) * (t<=x_filter[1])]
        fig.add_trace(
            go.Scatter(
                x=t[(t>=x_filter[0]) * (t<=x_filter[1])],
                y=ltemp-np.nanmean(ltemp),
                mode="lines",
                name=ln+" Crop"
            ),
            row=n_rows-obsNum-r-1, col=1
        )
        fig.update_yaxes(title_text=ln[:-1] + "- <"+ln[:-1] +">" , row=n_rows-r-1, col=1)
        

    fig.add_trace(
        go.Table(
            header=dict(
                values=df.columns,
                font=dict(size=10),
                align="left",
            ),
            cells=dict(
                values=[df[k].tolist() for k in df.columns],
                align = "left")
        ),
        row=1, col=1
    )
    
    return fig

#with open('config.json') as f:
#    d = json.load(f)

#rawProjectsPath = d['rawProjectsPath']
#procProjectsPath = d['procProjectsPath']
#allowedProjects = d['allowedProjects']

def make_3d_plot(t, x,y,z,dx,dy,dz):
    vecLenght = .4
    arroeTipSize = 1
    fig = go.Figure(data=go.Scatter3d(
        x=x, y=y, z=z,
        marker=dict(
            size=4,
            color=t,
            colorscale='Viridis',
            colorbar=dict(title='time')  # Add this line to show the colorbar
        ),
        line=dict(
            color='darkblue',
            width=2
        ),
        showlegend=False,  # Add this line to hide the line in the legend
        hovertemplate='Time: %{marker.color}<br>X: %{x}<br>Y: %{y}<br>Z: %{z}'  # Customize hover info
    ))
    for i in range(len(t)):
        fig.add_trace(
            go.Scatter3d(x=[x[i],x[i]+vecLenght*dx[i]], 
                         y=[y[i],y[i]+vecLenght*dy[i]],
                         z=[z[i],z[i]+vecLenght*dz[i]], 
                         mode='lines',
                         showlegend=False,
                         opacity = 0.2,
                         line=dict(color = 'darkblue'),
                         hoverinfo='skip'  # Disable hover
            )
            #go.Streamtube(x=x, y=y, z=z, u=10*dx, v=10*dy, w=10*dz)
        )
    fig.add_trace(
        go.Cone(
            x=x+vecLenght*dx,
            y=y+vecLenght*dy,
            z=z+vecLenght*dz,
            u= arroeTipSize*dx, #(t+0.01)*arroeTipSize*dx,
            v= arroeTipSize*dy, #(t+0.01)*arroeTipSize*dy,
            w= arroeTipSize*dz, #(t+0.01)*arroeTipSize*dz,
            colorscale='Viridis',
            sizemode="absolute",#"raw",
            showlegend=False,
            opacity=0.3,
            sizeref=4,
            showscale=False,  # Add this line to remove the colorbar
            hoverinfo='skip'  # Disable hover
        )
    )

    fig.update_layout(
        width=800,
        height=700,
        autosize=False,
        scene=dict(
            camera=dict(
                up=dict(
                    x=0,
                    y=1.,
                    z=0
                ),
                eye=dict(
                    x=0,
                    y=1.,
                    z=1.,
                )
            ),
            aspectratio = dict( x=1, y=1, z=1 ),
            aspectmode = 'manual'
        ),
    )
    return fig



def getVars(data):
    print('getVars',data)
    return (data)

def update_preprocessed_record_name(data):
    dff = json.loads(data) #= pd.read_json(data)
    project_name = dff['project_name']
    group_name = dff['group_name']
    record_name = dff['record_name']
    if record_name is not None:
        #print("record name",record_name)
        #rawRecord = projObj.get_record(project_name,group_name,record_name,'raw')
        childRecords = requests.get(f"{FASTAPI_URL}/record/children/raw/{project_name}/{group_name}/{record_name}").json()
        print('childRecords',childRecords)
        if len(childRecords) == 1:    
            return "Preprocessed record exist: "+ str(childRecords[0]['name']) 
        elif len(childRecords) > 1:    
            return "Preprocessed records exist: "+ str([cr.name for cr in childRecords]) 
    return "Preprocessed record exist: < None >"  

def load_edpoints(data):
    dff = json.loads(data) #dff = pd.read_json(data)
    project_name = dff['project_name']
    group_name = dff['group_name']
    record_name = dff['record_name']
    tmin = None
    tmax = None
    x_filter = [tmin,tmax]

    if record_name is not None:  
        dfS, timekey, pars = get_record_df('raw',project_name,group_name,record_name)  
        childRecords = requests.get(f"{FASTAPI_URL}/record/children/raw/{project_name}/{group_name}/{record_name}").json()
        if len(dfS.index):
            path = tsi.getPath(dfS,['posx','posy','posz'])
            t,x,y,z = path.T
            tmin = float( t.min() )
            tmax = float( t.max() )

            if len(childRecords) > 0:
                procRecord_name = childRecords[0]['name']
                procRecord_ver = childRecords[0]['ver']
                timeRange = requests.get(f"{FASTAPI_URL}/record/summary/proc/{project_name}/{group_name}/{procRecord_name}?ver={procRecord_ver}").json() #procRecord.pars
                print('timeRange',timeRange)
                tRangeMin = float( timeRange['t0'] ) 
                tRangeMax = float( timeRange['t1'] )
                x_filter = [tRangeMin,tRangeMax]
    print('x_filter',x_filter)
    return json.dumps({'values' : x_filter,'min':tmin,'max':tmax})#str(x_filter)

def update_slider(data, endpointsString):#,x_filter):
    print("update_slider",data)
    dff = json.loads(data) #= pd.read_json(data)
    #project_name = dff['project_name']
    #group_name = dff['group_name']
    record_name = dff['record_name']
    if record_name is not None:
        print("endpointsString", endpointsString )
        endpoints = json.loads(endpointsString)
        print("endpoint", endpoints['values'], endpoints['min'], endpoints['max'] )
        if endpoints['min'] == None:
            endpoints['min'] = 0.0
        if endpoints['max'] == None:
            endpoints['max'] = 3600.0
        if endpoints['values'][0] == None:
            endpoints['values'][0] = 0.0
            endpoints['values'][1] = 0.0
        return endpoints['values'], float(endpoints['min']), float(endpoints['max']) #float(x_filter[0]), float(x_filter[1])
    return [0.0, 3600.0], 0.0, 3600.0 #0.0, 3600.0

def load_plot(data,x_filter):
    dff = json.loads(data) #dff = pd.read_json(data)
    project_name = dff['project_name']
    group_name = dff['group_name']
    record_name = dff['record_name']
    if record_name is not None:
        #print("record name",record_name)
        dfS, timekey, pars = get_record_df('raw',project_name,group_name,record_name)

        print('columns',dfS.columns)
        nav = tsi.getVR(dfS)
        navAr = tsi.getAR(dfS)
        path = tsi.getPath(dfS,['posx','posy','posz'])
        fpath = None
        if 'fx' in dfS.columns: 
            fpath = tsi.getPath(dfS,['fx','fy','fz'])
        dpath = tsi.getPath(dfS,['dirx','diry','dirz'])
        if len(dfS.index):
            if isinstance(fpath,type(None)):
                t,x,y,z,dx,dy,dz,n = tsi.getSesVars(path,dpath,fpath,nav=nav)       
                t3,nAr = navAr.T   
                #print('t',t)
                plotLines = [x,y,z,dx,dy,dz]
                lineName = ['posx','posy','posz','dirx','diry','dirz']
            else:
                t,x,y,z,dx,dy,dz,fx,fy,fz,n = tsi.getSesVars(path,dpath,fpath,nav=nav)     
                t3,nAr = navAr.T 
                plotLines = [x,y,z,dx,dy,dz,fx,fy,fz]
                lineName = ['posx','posy','posz','dirx','diry','dirz','fx','fy','fz']


            #rawRecord.child_records[0].pars['t0'] == x_filter[0]

            return make_plot(dfS, t,plotLines,lineName,n,nAr,x_filter) 
    return px.scatter()

def load_3d_plot(data,x_filter):
    dff = json.loads(data) #dff = pd.read_json(data)
    project_name = dff['project_name']
    group_name = dff['group_name']
    record_name = dff['record_name']
    if record_name is not None:
        dfS, timekey, pars = get_record_df('raw',project_name,group_name,record_name)

        nav = tsi.getVR(dfS)
        navAr = tsi.getAR(dfS)
        path = tsi.getPath(dfS,['posx','posy','posz'])
        fpath = None
        dpath = tsi.getPath(dfS,['dirx','diry','dirz'])
        if len(dfS.index):
            t,x,y,z,dx,dy,dz,n = tsi.getSesVars(path,dpath,fpath=fpath,nav=nav)
            return make_3d_plot(t,x,y,z,dx,dy,dz) 
    return px.scatter()


def upload_proc_edpoints(x_filter):
    return json.dumps({'values' : x_filter})

def save_records(n_clicks,data,endpointsString): #, value):
    #records = g.records
    print('save_records') 
    x_filter = json.loads(endpointsString)["values"]
    print('n_clicks',n_clicks, x_filter )
    if n_clicks>0:
        print("Save ",data)
        dff = json.loads(data) #= pd.read_json(data)
        project_name = dff['project_name']
        group_name = dff['group_name']
        record_name = dff['record_name']
        print('dff',dff)
        if record_name is not None:
            # rawRecord = projObj.get_record(project_name,group_name,record_name,'raw')
            # procGroup = projObj.get_group(project_name,group_name,'proc',version='preprocessed-VR-sessions')
            dfS, timeKey, pars = get_record_df('raw',project_name,group_name,record_name)
            childRecords = requests.get(f"{FASTAPI_URL}/record/children/raw/{project_name}/{group_name}/{record_name}").json()
            kDf = dfS[ (dfS[timeKey]>=x_filter[0]) * (dfS[timeKey]<=x_filter[1])]
            if len(childRecords) == 0:
                #fName = record_name+'-preprocessed'
                #record_path = os.path.join(procGroup.path, 'preprocessed-VR-sessions',fName+'.csv')
                #procRecord = projObj.add_record(rawRecord,procGroup,fName,record_path, kDf, version='preprocessed-VR-sessions')
                version='preprocessed-VR-sessions'
                requests.post(f"{FASTAPI_URL}/record/proc/{project_name}/{group_name}/{record_name}/{version}", json=kDf.to_dict(orient="records"))
                #return f"Posted record in {project_name}/{group_name}/{record_name} at step proc version {version}" 
            if len(childRecords) == 1:  
                procRecord = childRecords[0]
                print('procRecord',procRecord)
                record_name = procRecord['name']
                record_ver = procRecord['ver']
                requests.put(f"{FASTAPI_URL}/record/proc/{project_name}/{group_name}/{record_name}/{record_ver}", json=kDf.to_dict(orient="records"))
                #return f"Puted record in {project_name}/{group_name}/{record_name} at step proc version {record_ver}" 
                #print('procRecord.group',procRecord.group.name,procRecord.group.pars,procRecord2.group.name,procRecord2.group.pars)
            #if not procRecord.group.parsFileExists():
            #    pars = rawRecord.group.putPar()
            # kDf.to_csv(procRecord.path,index=False,na_rep='NA') #(keeperPath+'/'+fname+'-preprocessed.csv',index=False,na_rep='NA')
            # procRecord.data = kDf
            # procRecord.putProcRecordInProcFile()
    return f"Puted record in {project_name}/{group_name}/{record_name} at step proc version {record_ver}" 
    

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


def init_callbacks(app):

    #dash_app.init_callback_vars(app)


    app.callback(
            Output('record-vars','children'),
            Input("variables", "data"),
        )(getVars)
    app.callback(
        Output("preprocessed-record-name", "children"),
        Input("variables", "data"), 
    )(update_preprocessed_record_name)
    app.callback(
        #Output("record-plot", "figure"),
        Output("x-slider-endpoints", "children"),
        Input("variables", "data"), 
        #Input("project-input1", "value"),
        #Input("dropdown-selection", "value"),
        #Input("dropdown-selection-records", "value"),
        #Input("x-slider", "value"),
    )(load_edpoints)
    app.callback(
        Output("x-slider", "value"),
        Output("x-slider", "min"),
        Output("x-slider", "max"), 
        #Output("x-slider", "marks"),  
        Input("variables", "data"),
        Input("x-slider-endpoints", "children"),
        #Input("x-slider", "value"),
    )(update_slider)
    app.callback(
        Output("record-plot", "figure"),
        #Output("x-slider-endpoints", "children"),
        Input("variables", "data"), 
        #Input("project-input1", "value"),
        #Input("dropdown-selection", "value"),
        #Input("dropdown-selection-records", "value"),
        Input("x-slider", "value"),
    )(load_plot)
    app.callback(
        Output("3d-record-plot", "figure"),
        Input("variables", "data"), 
        Input("x-slider", "value"),
    )(load_3d_plot)
    app.callback(
        Output("x-slider-proc-endpoints", "children"),
        Input("x-slider", "value")
    )(upload_proc_edpoints)
    app.callback(
       Output('container-button-basic', 'children'),
       Input('save-val', 'n_clicks'),
       State('variables', 'data'),
       State('x-slider-proc-endpoints', 'children'),
       prevent_initial_call=True
    )(save_records)
    # app.callback(
    #     Output("x-slider", "value"),
    #     Input('remove-rec', 'n_clicks'),
    #     State('variables', 'data'),
    #     prevent_initial_call=True
    # )(remove_record)


dash_app = dash.Dash(__name__, requests_pathname_prefix='/edit_record/') #,  external_stylesheets=[dbc.themes.BOOTSTRAP]  )

register_callbacks_vars(dash_app)
init_callbacks(dash_app)

layout1 = html.Div(
        [
            html.H1(children="Edit Record", style={"textAlign": "center"}),
            html.P(children="Select Roi in sessions from immersive and not-immersive explorations of Aton 3D " 
                              + "models which were captured with Merkhet. "),
            #dcc.Location(id='url2', refresh=False),
            html.P(id='record-vars'), #dcc.Store(id='variables')
            html.P(id="preprocessed-record-name", children= "Preprocessed record exist: < None >"),
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

        
