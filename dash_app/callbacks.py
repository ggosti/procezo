from dash import Input, Output, State

import requests
import json

import pandas as pd
import numpy as np

import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go


import timeSeriesInsightToolkit as tsi

with open('config.json') as f:
    d = json.load(f)
FASTAPI_URL_base = d['FASTAPI_URL_base']
FASTAPI_PORT = d['FASTAPI_PORT']
FASTAPI_URL = f"http://{FASTAPI_URL_base}:{FASTAPI_PORT}/api"

def register_callbacks(dash_app):
    # Populate project dropdown
    @dash_app.callback(
        Output("project-dropdown", "options"),
        Input("project-dropdown", "id")  # dummy trigger
    )
    def load_projects(_):
        r = requests.get(f"{FASTAPI_URL}/projects/raw").json()
        return [{"label": p["name"], "value": p["name"]} for p in r]

    # Populate group dropdown
    @dash_app.callback(
        Output("group-dropdown", "options"),
        Input("project-dropdown", "value")
    )
    def load_groups(project):
        #print("load_groups", project)
        if not project:
            return []
        r = requests.get(f"{FASTAPI_URL}/groups/raw/{project}").json()
        return [{"label": g["name"], "value": g["name"]} for g in r]

    # Populate file dropdown
    @dash_app.callback(
        Output("file-dropdown", "options"),
        [Input("project-dropdown", "value"),
        Input("group-dropdown", "value")]
    )
    def load_files(project, group):
        if not (project and group):
            return []
        records = requests.get(f"{FASTAPI_URL}/records/raw/{project}/{group}")
        return [{"label": r["name"], "value": r["name"]} for r in records.json()]

    # Plot the selected file
    @dash_app.callback(
        Output("timeseries-graph", "figure"),
        [Input("file-dropdown", "value")],
        [State("project-dropdown", "value"), State("group-dropdown", "value")]
    )
    def plot_timeseries(file, project, group):
        if not (project and group and file):
            return {}
        records = requests.get(f"{FASTAPI_URL}/records/raw/{project}/{group}")
        record = [r for r in records.json() if r["name"] == file][0]
        print("record", record, record["time_key"])
        rdata = requests.get(f"{FASTAPI_URL}/record/raw/{project}/{group}/{file}")
        data = rdata.json()["rows"]
        df = pd.DataFrame(data)
        df["timestamp"] = df[record["time_key"]]
        return px.line(df, x="timestamp", y="posx", title=f"{file} Time Series")
    pass


def register_callbacks_vars(app):
    @app.callback(
        Output("project-name", "children"),
        Output("group-name", "children"),
        Output("record-name", "children"),
        Input('url', 'pathname'),
    )
    def update_variable(pathname):
        project_name = '<None>'
        group_name = '<None>'
        record_name = '<None>'
        nameList = pathname.split('/')
        length = len(nameList)
        shift = 0
        if 'vars' in nameList: shift = shift + 1
        if 'edit_record' in nameList: shift = shift + 1
        if 'edit_group' in nameList: shift = shift + 1
        print('nameList update vars',nameList,length)
        try:
            if length > 1+shift:
                projects = requests.get(f"{FASTAPI_URL}/projects/raw").json()
                print('projects',projects)
                existing_project_names = [pr["name"] for pr in projects]
                print('existing_project_names',existing_project_names)
                project_name = '<None>' 
                if nameList[1+shift] in existing_project_names: #len(project_name) == 0:
                    project_name = nameList[1+shift]
                print('project_name',project_name,len(project_name))
            if length > 2+shift:
                groups = requests.get(f"{FASTAPI_URL}/groups/raw/{project_name}").json()
                existing_group_names = [gr["name"] for gr in groups  ]
                group_name = '<None>' 
                if nameList[2+shift] in existing_group_names:
                    group_name = nameList[2+shift]
            if length > 3+shift: 
                records = requests.get(f"{FASTAPI_URL}/records/raw/{project_name}/{group_name}").json()
                existing_records_names = [re["name"] for re in records]
                print('record_name update',record_name, nameList[3],existing_records_names)
                if not nameList[3+shift] == 'group_proc':
                    record_name = '<None>' 
                    if nameList[3+shift] in existing_records_names:
                        record_name = nameList[3+shift]
                print(record_name)
            return f"Project: {project_name}",f"Group: {group_name}",f"Record: {record_name}"
        except Exception as e:
            print('Error in update_variable',e)
            return f"Error in update_variable: {str(e)}"
    @app.callback(
        Output("variables", "data"),  
        Input('url', 'pathname'),
    )
    def update_group_variables(pathname):
        print("update_record_variables",pathname)
        nameList = pathname.split('/')
        length = len(nameList)
        print('nameList',nameList,length)
        d = {'project_name': None, 'group_name': None, 'record_name': None}
        shift = 0
        if 'vars' in nameList: shift = shift + 1
        if 'edit_record' in nameList: shift = shift + 1
        if 'edit_group' in nameList: shift = shift + 1
        if length > 1+shift:
            project_name = nameList[1+shift]
            print('project_name',project_name,len(project_name))
            if len(project_name) == 0:
                project_name = None
            d['project_name'] = project_name
        if length > 2+shift:
            group_name = nameList[2+shift]
            d['group_name'] = group_name
        if length > 3+shift: 
            record_name = nameList[3+shift]
            if not record_name == 'group_proc':
                d['record_name'] = record_name
            else:
                del d['record_name']
        #jsonD = json.dumps(d)
        #print(empty_json)
        return d #jsonD #pd.DataFrame().to_json()
    
    pass


#-------------------------------------
#Edit records
#--------------------------------------


def get_record(step,project_name,group_name,record_name,version=None):    
    url = f"{FASTAPI_URL}/record/{step}/{project_name}/{group_name}/{record_name}"
    if version is not None:
        url += f"?ver={version}"
    # Make the GET request
    response = requests.get(url)

    # Raise error if something went wrong
    response.raise_for_status()

    # Convert JSON response to DataFrame
    data = response.json()

    return data

def get_record_df(step,project_name,group_name,record_name,version=None):
    data = get_record(step,project_name,group_name,record_name,version)
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

    # show VR and AR
    if navAr is None:
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



def register_callbacks_records(app):

    @app.callback(
        Output('record-vars','children'),
        Input("variables", "data"),
    )
    def getVars(data):
        print("Starting getVars callback")
        print('getVars',data)
        return 
    
    @app.callback(
        Output("preprocessed-record-name", "children"),
        Output("processed-record", "data"),
        Input("variables", "data"), 
    )
    def update_preprocessed_record_name(data):
        #dff = json.loads(data) #= pd.read_json(data)
        print("Starting update_preprocessed_record_name callback")
        project_name = data['project_name']
        group_name = data['group_name']
        record_name = data['record_name']
        print("record name",record_name)
        if record_name is not None:
            #print("record name",record_name)
            #rawRecord = projObj.get_record(project_name,group_name,record_name,'raw')
            childRecords = requests.get(f"{FASTAPI_URL}/record/children/raw/{project_name}/{group_name}/{record_name}").json()
            print('childRecords',childRecords)
            if len(childRecords) == 1:    
                return "Preprocessed record exist: "+ str(childRecords[0]['name']), childRecords
            elif len(childRecords) > 1:    
                return "Preprocessed records exist: "+ str([cr.name for cr in childRecords]) , childRecords
        return "Preprocessed record exist: < None >" , []

    @app.callback(
        Output("record-points","data"),
        Input("variables", "data"),
    )
    def lead_record_points(data):
        print("Starting lead_record_points callback")
        #dff = json.loads(data) #= pd.read_json(data)
        project_name = None
        group_name = None
        record_name = None
        try:
            #data = app.layout['variables'].data
            project_name = data['project_name']
            group_name = data['group_name']
            record_name = data['record_name']
        except Exception as e:
            print('Error in lead_record_points',e)
        
        if record_name is not None:
            step = 'raw'
            url = f"{FASTAPI_URL}/record/{step}/{project_name}/{group_name}/{record_name}"
            #if version is not None:
            #    url += f"?ver={version}"
            # Make the GET request
            response = requests.get(url)

            # Raise error if something went wrong
            response.raise_for_status()

            # Convert JSON response to DataFrame
            record = response.json()
            #df = pd.DataFrame(data["rows"])
            #timekey = data["timeKey"]
            #pars = data["pars"]
            return record
        return {}

    @app.callback(
        Output("x-slider-endpoints", "children"),
        State("variables", "data"),
        Input("record-points", "data"),
        Input("processed-record", "data"),
        prevent_initial_call=True
    )
    def load_edpoints(data, record, childRecords):
        #dff = json.loads(data) #dff = pd.read_json(data)
        project_name = data['project_name']
        group_name = data['group_name']
        record_name = data['record_name']
        tmin = None
        tmax = None
        x_filter = [tmin,tmax]
        print("-> load_edpoints ", record.keys())

        if record_name is not None:  
            #dfS, timekey, pars = get_record_df('raw',project_name,group_name,record_name)  
            #childRecords = processed_record_list #requests.get(f"{FASTAPI_URL}/record/children/raw/{project_name}/{group_name}/{record_name}").json()
            print('childRecords',childRecords)
            #dfS = childRecords[0]['data'] if len(childRecords) > 0 else None
            dfS = pd.DataFrame(record["rows"])
            #timekey = record["timeKey"]
            #pars = record["pars"]
            #print('dfS',dfS)
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

    @app.callback(
        Output("x-slider", "value"),
        Output("x-slider", "min"),
        Output("x-slider", "max"), 
        Input("variables", "data"),
        Input("x-slider-endpoints", "children"),
    ) #(update_slider)
    def update_slider(data, endpointsString):#,x_filter):
        print("update_slider",data)
        #dff = json.loads(data) #= pd.read_json(data)
        #project_name = dff['project_name']
        #group_name = dff['group_name']
        record_name = data['record_name']
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
    
    @app.callback(
        Output("record-plot", "figure"),
        #Output("x-slider-endpoints", "children"),
        Input("variables", "data"), 
        Input("record-points", "data"),
        #Input("project-input1", "value"),
        #Input("dropdown-selection", "value"),
        #Input("dropdown-selection-records", "value"),
        Input("x-slider", "value"),
    )#(load_plot)
    def load_plot(data, record, x_filter):
        #dff = json.loads(data) #dff = pd.read_json(data)
        project_name = data['project_name']
        group_name = data['group_name']
        record_name = data['record_name']
        if record_name is not None:
            #print("record name",record_name)
            #dfS, timekey, pars = get_record_df('raw',project_name,group_name,record_name)
            dfS = pd.DataFrame(record["rows"])

            print('columns',dfS.columns)

            nav = None
            navAr = None
            if 'nav' in dfS.columns:
                nav = tsi.getVR(dfS)
                _,n = nav.T
                navAr = tsi.getAR(dfS)
                _,nAr = navAr.T
            path = tsi.getPath(dfS,['posx','posy','posz'])
            fpath = None
            if 'fx' in dfS.columns: 
                fpath = tsi.getPath(dfS,['fx','fy','fz'])
            dpath = tsi.getPath(dfS,['dirx','diry','dirz'])
            if len(dfS.index):
                if isinstance(fpath,type(None)):
                    #t,x,y,z,dx,dy,dz,n = tsi.getSesVars(path,dpath,fpath,nav=nav)    
                    t,x,y,z = path.T
                    _, dx,dy,dz = dpath.T   
                    #_, nAr = navAr.T   
                    #print('t',t)
                    plotLines = [x,y,z,dx,dy,dz]
                    lineName = ['posx','posy','posz','dirx','diry','dirz']
                else:
                    #t,x,y,z,dx,dy,dz,fx,fy,fz,n = tsi.getSesVars(path,dpath,fpath,nav=nav)     
                    t,x,y,z = path.T
                    _,fx,fy,fz = fpath.T
                    _, dx,dy,dz = dpath.T   
                    #t3,nAr = navAr.T 
                    plotLines = [x,y,z,dx,dy,dz,fx,fy,fz]
                    lineName = ['posx','posy','posz','dirx','diry','dirz','fx','fy','fz']


                return make_plot(dfS, t,plotLines,lineName,n,nAr,x_filter) 
        return px.scatter()
        

    @app.callback(
        Output("3d-record-plot", "figure"),
        Input("variables", "data"), 
        Input("record-points", "data"),
        Input("x-slider", "value"),
    )#(load_3d_plot)
    def load_3d_plot(data, record, x_filter):
        print("Starting load_3d_plot callback")
        #dff = json.loads(data) #dff = pd.read_json(data)
        project_name = data['project_name']
        group_name = data['group_name']
        record_name = data['record_name']
        if record_name is not None:
            #dfS, timekey, pars = get_record_df('raw',project_name,group_name,record_name)
            dfS = pd.DataFrame(record["rows"])

            nav = tsi.getVR(dfS)
            navAr = tsi.getAR(dfS)
            path = tsi.getPath(dfS,['posx','posy','posz'])
            fpath = None
            dpath = tsi.getPath(dfS,['dirx','diry','dirz'])
            if len(dfS.index):
                t,x,y,z,dx,dy,dz,n = tsi.getSesVars(path,dpath,fpath=fpath,nav=nav)
                return make_3d_plot(t,x,y,z,dx,dy,dz) 
        return px.scatter()
    
    @app.callback(
        Output("x-slider-proc-endpoints", "children"),
        Input("x-slider", "value")
    )#(upload_proc_edpoints)
    def upload_proc_edpoints(x_filter):
        print("Starting upload_proc_edpoints callback")
        return json.dumps({'values' : x_filter})
    
    @app.callback(
       Output('container-button-basic', 'children'),
       Input('save-val', 'n_clicks'),
       State('variables', 'data'),
       State('record-points', 'data'),
       State("processed-record", "data"),
       State('x-slider-proc-endpoints', 'children'),
       prevent_initial_call=True
    )#(save_records)
    def save_records(n_clicks, data, record, childRecords, endpointsString): #, value):
        print("Starting save_records callback")
        #records = g.records
        print('save_records') 
        x_filter = json.loads(endpointsString)["values"]
        print('n_clicks',n_clicks, x_filter )
        if n_clicks>0:
            try:
                print("Save ",data)
                #dff = json.loads(data) #= pd.read_json(data)
                project_name = data['project_name']
                group_name = data['group_name']
                record_name = data['record_name']
                print('data',data)
                if record_name is not None:
                    # rawRecord = projObj.get_record(project_name,group_name,record_name,'raw')
                    # procGroup = projObj.get_group(project_name,group_name,'proc',version='preprocessed-VR-sessions')
                    #dfS, timeKey, pars = get_record_df('raw',project_name,group_name,record_name)
                    dfS = pd.DataFrame(record["rows"])
                    timeKey = record["timeKey"]
                    print('timeKey',timeKey)
                    #childRecords = requests.get(f"{FASTAPI_URL}/record/children/raw/{project_name}/{group_name}/{record_name}").json()
                    kDf = dfS[ (dfS[timeKey]>=x_filter[0]) * (dfS[timeKey]<=x_filter[1])]
                    if len(childRecords) == 0:
                        #fName = record_name+'-preprocessed'
                        #record_path = os.path.join(procGroup.path, 'preprocessed-VR-sessions',fName+'.csv')
                        #procRecord = projObj.add_record(rawRecord,procGroup,fName,record_path, kDf, version='preprocessed-VR-sessions')
                        record_ver='preprocessed-VR-sessions'
                        requests.post(f"{FASTAPI_URL}/record/proc/{project_name}/{group_name}/{record_name}/{record_ver}", json=kDf.to_dict(orient="records"))
                        return f"Posted record in {project_name}/{group_name}/{record_name} at step proc version {record_ver}" 
                    if len(childRecords) == 1:  
                        procRecord = childRecords[0]
                        print('procRecord',procRecord)
                        record_name = procRecord['name']
                        record_ver = procRecord['ver']
                        requests.put(f"{FASTAPI_URL}/record/proc/{project_name}/{group_name}/{record_name}/{record_ver}", json=kDf.to_dict(orient="records"))
                        return f"Puted record in {project_name}/{group_name}/{record_name} at step proc version {record_ver}" 
                        #print('procRecord.group',procRecord.group.name,procRecord.group.pars,procRecord2.group.name,procRecord2.group.pars)
                    #if not procRecord.group.parsFileExists():
                    #    pars = rawRecord.group.putPar()
                    # kDf.to_csv(procRecord.path,index=False,na_rep='NA') #(keeperPath+'/'+fname+'-preprocessed.csv',index=False,na_rep='NA')
                    # procRecord.data = kDf
                    # procRecord.putProcRecordInProcFile()
            except Exception as e:
                return f"Error: {str(e)}"
        return "Click to save record."
    
    @app.callback(
        #Output("x-slider", "value"),
        Output('container-button-remove', 'children'),
        Input('remove-rec', 'n_clicks'),
        State('variables', 'data'),
        prevent_initial_call=True
    )#(remove_record)
    def remove_record(n_clicks, data):
        print("Starting remove_record callback")
        if n_clicks:
            try:
                #dff = json.loads(data)
                project_name = data['project_name']
                group_name = data['group_name']
                record_name = data['record_name']
                version = 'preprocessed-VR-sessions'
                resp = requests.delete(
                    f"{FASTAPI_URL}/record/proc/{project_name}/{group_name}/{record_name}-preprocessed/{version}",
                    timeout=5  # Add a timeout to avoid hanging forever
                )
                if resp.status_code == 200:
                    return "Record removed successfully."
                else:
                    return f"Failed to remove record: {resp.status_code}"
            except Exception as e:
                return f"Error: {str(e)}"
        return "Click to remove record."
    pass


#-------------------------------------
#Edit group 
#--------------------------------------

def getPaths(dfSs,panoramic = False):
    if not panoramic:
        #paths=tsi.getPaths(ids,dfSs,['posx','posy','posz'])
        paths = [tsi.getPath(dfS,['posx','posy','posz']) for dfS in dfSs]
        #_,x,y,z = np.vstack(paths).T
    else:
        #paths = tsi.getPaths(ids,dfSs,['dirx','diry','dirz'])
        paths = [tsi.getPath(dfS,['dirx','diry','dirz']) for dfS in dfSs]
        #_,u,v,w = np.vstack(paths).T
    #paths = ma.getVarsFromSession(pathSes,['pos'])[0]
    #ids, fileNames, [paths,dpaths] = ma.getVarsFromSession(pathSes,['pos','dir'])
    #if panoramic: paths=dpaths
    return paths

def getDurationAndVariability(paths):
    #thTime = 35
    #thVar = 0.1#1.#0.1#1.#0.4 #2.5

    totTimes = []
    totVars = []
    for path in paths:
        t,x,y,z = path.T
        totTime = t[-1]-t[0]
        totTimes.append(totTime)
        totVar = np.var(x)+np.var(y)+np.var(z)
        totVars.append(totVar)
    return totTimes,totVars

def myScatterEmpty(xlab,ylab):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
            #x = x,
            #y = y,
            xaxis = 'x',
            yaxis = 'y',
            mode = 'markers',
            #marker = dict(
            #    color = 'rgba(0,0,0,0.3)',
            #    size = 3
            #)
        ))
    fig.add_trace(go.Histogram(
            #y = y,
            xaxis = 'x2',
            marker = dict(
                color = 'rgba(0,0,0,1)'
            )
        ))
    fig.add_trace(go.Histogram(
            #x = x,
            yaxis = 'y2',
            marker = dict(
                color = 'rgba(0,0,0,1)'
            )
        ))
        
    fig.update_layout(
        autosize = False,
        xaxis = dict(
            zeroline = False,
            domain = [0,0.85],
            showgrid = False,
            title = xlab  # Add x-axis label
        ),
        yaxis = dict(
            zeroline = False,
            domain = [0,0.85],
            showgrid = False,
            title = ylab  # Add y-axis label
        ),
        xaxis2 = dict(
            zeroline = False,
            domain = [0.85,1],
            showgrid = False
        ),
        yaxis2 = dict(
            zeroline = False,
            domain = [0.85,1],
            showgrid = False
        ),
        height = 900,
        width = 900,
        bargap = 0,
        hovermode = 'closest',
    )
    return fig

def myScatter(x,y,xlab,ylab,names):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
            x = x,
            y = y,
            xaxis = 'x',
            yaxis = 'y',
            mode = 'markers',
            #marker = dict(
            #    color = 'rgba(0,0,0,0.3)',
            #    size = 3
            #)
            hovertext = names
        ))
    fig.add_trace(go.Histogram(
            y = y,
            xaxis = 'x2',
            nbinsy=100 ,
            #marker = dict(
            #    color = 'rgba(0,0,0,1)'
            #)
        ))
    fig.add_trace(go.Histogram(
            x = x,
            yaxis = 'y2',
            nbinsx=100 ,
            #marker = dict(
            #    color = 'rgba(0,0,0,1)'
            #)
        ))
        
    fig.update_layout(
        autosize = False,
        xaxis = dict(
            zeroline = False,
            domain = [0,0.85],
            showgrid = False,
            title = xlab  # Add x-axis label
        ),
        yaxis = dict(
            zeroline = False,
            domain = [0,0.85],
            showgrid = False,
            title = ylab  # Add y-axis label
        ),
        xaxis2 = dict(
            zeroline = False,
            domain = [0.85,1],
            showgrid = False
        ),
        yaxis2 = dict(
            zeroline = False,
            domain = [0.85,1],
            showgrid = False
        ),
        height = 900,
        width = 900,
        bargap = 0,
        hovermode = 'closest',
    )
    return fig
    


def register_callbacks_group(app):

    @app.callback(
        Output("group-vars","children"),
        Input("variables", "data"),
    )
    def getVars2(data):
        print("data getVars2",data)
        return (data)
    
    @app.callback(
        Output("preprocessed-record-names", "children"),
        Input("variables", "data"),
    )
    def get_preprocessed_record_names(data):
        #data = json.loads(data) 
        project_name = data["project_name"]
        group_name = data["group_name"]
        print('get_preprocessed_record_names',group_name)
        if isinstance(group_name, str):#project_name in allowedProjects: 
            #records = projObj.get_recods_in_project_and_group(project_name,group_name,step='proc',version='preprocessed-VR-sessions')
            records = requests.get(f"{FASTAPI_URL}/records/proc/{project_name}/{group_name}?ver=preprocessed-VR-sessions").json()
            fileNames = [re["name"] for re in records]
            print('records',fileNames)
            #fileNames, dfSs  = loadData(group_name,project_name,version='preprocessed-VR-sessions')
            return str(fileNames)
        else:
            return str(None)
        
    @app.callback(
        Output("panoramic-checklist","value"),
        Output("is-panoramic","data"),
        Input("variables", "data"),
    )
    def setPanoramiCheckValuse(data):
        print("Starting setPanoramiCheckValuse callback",data)
        project_name = data['project_name']
        group_name = data['group_name']
        #rawGroup = projObj.get_group(project_name,group_name,'raw')
        #pregatedGroup = projObj.get_group(project_name,group_name,'proc',version='preprocessed-VR-sessions')
        pregatedGroup = requests.get(f"{FASTAPI_URL}/group/proc/{project_name}/{group_name}/preprocessed-VR-sessions").json()
        if pregatedGroup["panoramic"]:
            value = ["Panoramic"]
            data = True
        else:
            value = []
            data = False
        print('pregatedGroup',pregatedGroup,value)
        return value, data #json.dumps({'panoramic': True}) if 'Panoramic' in value else json.dumps({'panoramic': False})
    
    @app.callback(
        Output("panoramic-checklist-dialog","children"),
        State("variables", "data"),
        Input("panoramic-checklist","value"),
        prevent_initial_call=True
    )
    def patchPanoramiCheckValuse(data, value):
        #dff = data #json.loads(data)
        project_name = data['project_name']
        group_name = data['group_name']
        print("check valuse",value)
        if 'Panoramic' in value:
            jsonData = json.dumps({'panoramic': True})
        else:
            jsonData = json.dumps({'panoramic': False})
        print("jsonData",jsonData)
        resp = requests.patch(
            f"{FASTAPI_URL}/group/proc/{project_name}/{group_name}/preprocessed-VR-sessions",
            data=jsonData,
            headers={"Content-Type": "application/json"}
        )
        if resp.status_code == 200:
            return "Panoramic value updated successfully."
        else:
            return f"Failed to update panoramic value: {resp.status_code} - {resp.text}"

    @app.callback(
        Output("points","data"),
        State("is-panoramic","data"),
        Input("variables", "data"),
    )
    def load_points(is_panoramic, data):
        print("Starting load_points callback")
        project_name = data['project_name']
        group_name = data['group_name']
        if isinstance(group_name, str):
            records = requests.get(f"{FASTAPI_URL}/records/proc/{project_name}/{group_name}?ver=preprocessed-VR-sessions").json()
            #dfSs = [re.data for re in procGroup.records]
            #fileNames = [re["name"] for re in records]
            step = 'proc'
            dfSs = []
            fileNames = []
            for re in records:
                print('record',re['name'],re['ver'])
                #dfS = requests.get(f"{FASTAPI_URL}/record/proc/{project_name}/{group_name}/{re['name']}?ver={re['ver']}").json()
                record_name = re['name']
                dfS, timekey, pars  = get_record_df(step,project_name,group_name,record_name,version="preprocessed-VR-sessions")
                dfSs.append(dfS)
                fileNames.append(record_name)

            #gatedGroupRecords = requests.get(f"{FASTAPI_URL}/records/proc/{project_name}/{group_name}?ver=preprocessed-VR-sessions-gated").json()
            #gatedFileNames = []
            #for re in gatedGroupRecords:
            #    print('gated record',re['name'],re['ver'])
            #    gatedFileNames.append(re['name'])
            paths = getPaths(dfSs,panoramic=is_panoramic)
            totTimes,totVars = getDurationAndVariability(paths)
            dfScalar = pd.DataFrame({'variance':totVars,'session time (s)':totTimes,'fileNames':fileNames} )
            x = dfScalar['session time (s)']
            y = dfScalar['variance']
            print('x',x)
            print('y',y)
            print('fileNames',fileNames)
        points = {'x': x.tolist(), 
                  'y': y.tolist(), 
                  'names': fileNames,
                  'xmax': float(x.max()), 'xmin': float(x.min()), 
                  'ymax': float(y.max()), 'ymin': float(y.min())}#,
                  #'gatedFileNames':gatedFileNames}
        print("points",points)
        return points 

    @app.callback(
        Output("x-slider-2", "min"),
        Output("x-slider-2", "max"), 
        Output("x-slider-2", "marks"),  
        Output("y-slider", "min"),
        Output("y-slider", "max"), 
        Output("y-slider", "marks"),
        State("is-panoramic","data"),
        State("variables", "data"),
        Input("points", "data")
    )
    def update_slider(is_panoramic, data,points):
        project_name = data['project_name']
        group_name = data['group_name']
        print("is_panoramic",is_panoramic)
        print("Starting update_slider callback")
        print('points',points)
        xmin = points['xmin']
        xmax = points['xmax']
        ymin = points['ymin']
        ymax = points['ymax']
        x_filter = [xmin, xmax]
        y_filter = [ymin, ymax]

        return xmin, xmax, {xmin: str(xmin), xmax: str(xmax)}, ymin, ymax, {ymin: str(ymin), ymax: str(ymax)}
    
    @app.callback(
        Output("x-slider-output", "children"), 
        Output("y-slider-output", "children"),
        Input("variables", "data"),
        Input("x-slider-2", "value"),
        Input("y-slider", "value"),
    )
    def update_slider_output_text(data,x_filter = [0., 360.], y_filter = [0., 2.]):
        if isinstance(data, dict):
            #project_name = data['project_name']
            group_name = data['group_name']
            if isinstance(group_name, str):
                print('x_filter',x_filter)
                print('y_filter',y_filter)
                x_text = f"[{x_filter[0]}, {x_filter[1]}]"
                y_text = f"[{y_filter[0]}, {y_filter[1]}]"
                return x_text, y_text
        x_text = f"None"
        y_text = f"None"
        return x_text, y_text
        
        

    @app.callback(
        Output("scatter-plot", "figure"), 
        State("variables", "data"),
        Input("points", "data"),
        State("panoramic-checklist","value"),
        Input("x-slider-2", "value"),
        Input("y-slider", "value"),
    )
    def update_graph(data,points,value,x_filter = [0., 360.], y_filter = [0., 2.]):
        #print('data 2',data,type(data))
        project_name = data["project_name"]
        group_name = data["group_name"]
        #print('x_filter',x_filter)
        print('points 2',points,type(points))
        #print('update_graph',group_name)
        panoramic = False
        if "Panoramic" in value:
            panoramic = True
        if isinstance(points, dict):
            x = points['x']
            y = points['y']
            names = points['names']

            fig = myScatter(x,y,xlab = 'session time (s)' ,ylab = 'variance',names = names)  #px.scatter(dfScalar,x='session time (s)', y='variance', marginal_x="histogram", marginal_y="histogram",hover_data=['fileNames'])
            fig.add_shape(type="rect",
                x0=x_filter[0], y0=y_filter[0], x1=x_filter[1], y1=y_filter[1],
                line=dict(
                    color="RoyalBlue",
                    width=2,
                ),
                fillcolor="LightSkyBlue",
                layer="below",
            )


            return fig
        else:
            fig = myScatterEmpty(xlab = 'session time (s)' ,ylab = 'variance')
            return fig #, str(x_filter), 0.0, 360.0, {0: '0', 360.: '360'}, str(y_filter), 0.0, 2.0, {0: '0.0', 2.: '2.0'}

    @app.callback(
        Output("preprocessed-gated-record-names", "children"),
        Input("variables", "data"),
    )
    def get_saved_preprocessed_gated_record_names(data):
        project_name = data["project_name"]
        group_name = data["group_name"]
        print(group_name)
        if isinstance(group_name, str):#project_name in allowedProjects: 
            #fileNames, dfSs  = loadData(group_name,project_name,version='preprocessed-VR-sessions')
            #records = projObj.get_recods_in_project_and_group(project_name,group_name,step='proc',version='preprocessed-VR-sessions-gated')
            records = requests.get(f"{FASTAPI_URL}/records/proc/{project_name}/{group_name}?ver=preprocessed-VR-sessions-gated").json()
            fileNames = [re['name'] for re in records]
            
            return str(fileNames)
        else:
            return str(None)
        
    @app.callback(
        Output("preprocessed-gated-selected-record-names", "children"),
        State("variables", "data"),
        Input("points", "data"),
        State("panoramic-checklist","value"),
        Input("x-slider-2", "value"),
        Input("y-slider", "value"),
        
    )
    def get_selected_preprocessed_gated_record_names(data,points,value,xRange2,yRange2):
        project_name = data["project_name"]
        group_name = data["group_name"]
        #print(group_name)
        thTime0,thTime1 = xRange2 #json.loads(xRange)
        thVar0,thVar1 = yRange2#json.loads(yRange)
        print('selected preprocessed-gated record names')
        print('xRange',xRange2,thTime0,thTime1)
        print('yRange',yRange2)
        panoramic = False
        if "Panoramic" in value:
            panoramic = True
        if isinstance(points, dict):
            xs = points['x']
            ys = points['y']
            names = points['names']
            ungatedFileNames = []
            for fName,y,x in zip(names, ys, xs):
                print('fName',fName)
                if (y >= thVar0) and (y <= thVar1) and (x >= thTime0) and (x <= thTime1):
                    ungatedFileNames.append(fName)
                    print('session in ',fName)
                    #assert session in d['preprocessedVRsessions'], "session not in preprocessedVRsessions "+session
                    #d['preprocessedVRsessions-gated'][session] = d['preprocessedVRsessions'][session]
                    #if 'ID' in dfS.columns: dfS = dfS.drop(columns=['ID', 'filename'])
                    #dfS.to_csv(gatedPath+'/'+session+'-preprocessed.csv',index=False,na_rep='NA')
                else:
                    print('session out',fName)
                    #tsi.drawPath(path, dpath=None, BBox=None)
            return json.dumps(ungatedFileNames)
        else:
            return json.dumps([])
        
    @app.callback(
        Output('button-basic-responce', 'children'),
        State('variables', 'data'),
        State("points", "data"),
        State("preprocessed-gated-selected-record-names", "children"),
        State("x-slider-output", "children"),
        State("y-slider-output", "children"),
        Input('save-gate', 'n_clicks'),
        prevent_initial_call=True
    )
    def save_selected_records(data, points,selected_rec_names,xRange,yRange, n_clicks):
        #print('n_clicks',n_clicks )
        #print('data',data )
        #print('selected_rec_names',selected_rec_names )
        selectedNames = json.loads(selected_rec_names)
        #print('selected_rec_names',selectedNames )
        thTime0,thTime1 = json.loads(xRange)
        thVar0,thVar1 = json.loads(yRange)

        if n_clicks>0:
            print("Save ",data)
            project_name = data['project_name']
            group_name = data['group_name']
            
            gatedGroupRecords = requests.get(f"{FASTAPI_URL}/records/proc/{project_name}/{group_name}?ver=preprocessed-VR-sessions-gated").json()
            gatedFileNames = []
            for re in gatedGroupRecords:
                print('gated record',re['name'],re['ver'])
                gatedFileNames.append(re['name'])

            #print('gatedGroupRecords',gatedGroupRecords)
            
            for record in gatedGroupRecords:
                try:
                    record_name = record["name"]
                    print('record_name to remove',record_name)
                    version = "preprocessed-VR-sessions-gated"
                    resp = requests.delete(
                        f"{FASTAPI_URL}/record/proc/{project_name}/{group_name}/{record_name}/{version}",
                        timeout=5  # Add a timeout to avoid hanging forever
                    )
                    if resp.status_code == 200:
                        print("Record removed successfully.")
                    else:
                        print(f"Failed to remove record: {resp.status_code}")
                except Exception as e:
                    print(f"Error removing records: {str(e)}")
            #points["gatedFileNames"] = []
            #print('gatedGroupRecords is empty? ',points["gatedFileNames"])

            d = requests.get(f"{FASTAPI_URL}/group/proc/{project_name}/{group_name}/preprocessed-VR-sessions").json()
            #print('ungatedGroup pars',ungatedGroup.path,ungatedGroup.pars_path) 
            #print('ungatedGroup pars',ungatedGroup.pars) 
            #print(d['preprocessedVRsessions'])
            d['gated'] = {'thVar >=':thVar0,'thVar <=':thVar1,'thTime >=':thTime0,'thTime <=':thTime1}
            #d['preprocessedVRsessions-gated'] = {}
            print('removed records from group')
            print('d',d)

            try:
                #newGatedRecords = []
                for fName in selectedNames:
                    print('fName post',fName)
                    #record =projObj.get_record(project_name,group_name,fName,'proc',version='preprocessed-VR-sessions')
                    version='preprocessed-VR-sessions'
                    record_name = fName
                    #record = requests.get(f"{FASTAPI_URL}/record/proc/{project_name}/{group_name}/{record_name}?ver={version}")
                    dfS, timeKey, pars = get_record_df('proc',project_name,group_name,record_name,version=version)
                    childRecords = requests.get(f"{FASTAPI_URL}/record/children/proc/{project_name}/{group_name}/{record_name}?ver={version}").json()
                    #print('childRecords',childRecords)

                    if len(childRecords) == 0:
                        #fName = record_name+'-preprocessed'
                        #record_path = os.path.join(procGroup.path, 'preprocessed-VR-sessions',fName+'.csv')
                        #procRecord = projObj.add_record(rawRecord,procGroup,fName,record_path, kDf, version='preprocessed-VR-sessions')
                        record_ver='preprocessed-VR-sessions-gated'
                        resp = requests.post(f"{FASTAPI_URL}/record/proc/{project_name}/{group_name}/{record_name}/{record_ver}", json=dfS.to_dict(orient="records"))
                        print(f"Posted record in {project_name}/{group_name}/{record_name} at step proc version {version}") 
                        #newGatedRecords.appenrd(record_name)
                #points['gatedFileNames'] = newGatedRecords
            except Exception as e:
                print(f"Error: {str(e)}")
            
            try:
                print('patch d',d)
                resp = requests.patch(
                    f"{FASTAPI_URL}/group/proc/{project_name}/{group_name}/preprocessed-VR-sessions",
                    data=json.dumps(d),
                    headers={"Content-Type": "application/json"}
                )
                print('patch resp',resp)
            except Exception as e:
                print( f"Error: {str(e)}")
            #tsi.writeJson(pregatedGroup.pars_path,d)
            return "Saved!"


    pass