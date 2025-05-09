from dash import Input, Output, State

import requests
import json

import pandas as pd
import numpy as np
import plotly.express as px

import os

import timeSeriesInsightToolkit as tsi

FASTAPI_URL = "http://localhost:8000/api"

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
        jsonD = json.dumps(d)
        #print(empty_json)
        return jsonD #pd.DataFrame().to_json()
    
    pass


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
        #print(data)
        return (data)
    
    @app.callback(
        Output("preprocessed-record-names", "children"),
        Input("variables", "data"),
    )
    def get_preprocessed_record_names(data):
        data = json.loads(data) 
        project_name = data["project_name"]
        group_name = data["group_name"]
        print('get_preprocessed_record_names',group_name)
        if isinstance(group_name, str):#project_name in allowedProjects: 
            #records = projObj.get_recods_in_project_and_group(project_name,group_name,step='proc',version='preprocessed-VR-sessions')
            records = requests.get(f"{FASTAPI_URL}/records/proc/{project_name}/{group_name}?ver=preprocessed-VR-sessions").json()
            fileNames = [re["name"] for re in records]
            #fileNames, dfSs  = loadData(group_name,project_name,version='preprocessed-VR-sessions')
            return str(fileNames)
        else:
            return str(None)
        
    @app.callback(
        Output("panoramic-checklist","value"),
        Input("variables", "data"),
    )
    def setPanoramiCheckValuse(data):
        dff = json.loads(data) #= pd.read_json(data)
        project_name = dff['project_name']
        group_name = dff['group_name']
        value=[]
        #rawGroup = projObj.get_group(project_name,group_name,'raw')
        #pregatedGroup = projObj.get_group(project_name,group_name,'proc',version='preprocessed-VR-sessions')
        pregatedGroup = requests.get(f"{FASTAPI_URL}/group/proc/{project_name}/{group_name}/preprocessed-VR-sessions").json()
        value = pregatedGroup["panoramic"]
        return value
    
    # @app.callback(
    #     State("variables", "data"),
    #     Input("panoramic-checklist","value"),
    # )
    # def getPanoramiCheckValuse(data,value):
    #     dff = json.loads(data) #= pd.read_json(data)
    #     project_name = dff['project_name']
    #     group_name = dff['group_name']
    #     #rawGroup = projObjInt.get_group(project_name,group_name,'raw')
    #     pregatedGroup = projObj.get_group(project_name,group_name,'proc',version='preprocessed-VR-sessions')
    #     if pregatedGroup.parsFileExists():
    #         d = pregatedGroup.loadPars()
    #         if 'panoramic' in d:
    #             value = ["Panoramic"]
    #     #print(value)
    #     if "Panoramic" in value:
    #         #print("Panoramic")
    #         #rawGroup.set_panoramic(True)
    #         pregatedGroup.set_panoramic(True)
    
    # @app.callback(
    #     Output("scatter-plot", "figure"), 
    #     Output("x-slider-output", "children"), 
    #     Output("x-slider-2", "min"),
    #     Output("x-slider-2", "max"), 
    #     Output("x-slider-2", "marks"), 
    #     Output("y-slider-output", "children"), 
    #     Output("y-slider", "min"),
    #     Output("y-slider", "max"), 
    #     Output("y-slider", "marks"),
    #     Input("variables", "data"),
    #     Input("panoramic-checklist","value"),
    #     Input("x-slider-2", "value"),
    #     Input("y-slider", "value"),
    # )
    # def update_graph(data,value,x_filter = [0., 360.], y_filter = [0., 2.]):
    #     data = json.loads(data) 
    #     project_name = data["project_name"]
    #     group_name = data["group_name"]
    #     #print('x_filter',x_filter)
    #     print('update_graph',group_name)
    #     panoramic = False
    #     if "Panoramic" in value:
    #         panoramic = True
    #     if isinstance(group_name, str):#project_name in allowedProjects: 
    #         procGroup = projObj.get_group(project_name,group_name,'proc',version='preprocessed-VR-sessions')
    #         dfSs = [re.data for re in procGroup.records]
    #         fileNames = [re.name for re in procGroup.records]
    #         #fileNames, dfSs = loadData(group_name,project_name,version='preprocessed-VR-sessions')
    #         #dff = df[df.country == value]
    #         paths = getPaths(dfSs,panoramic=panoramic)
    #         totTimes,totVars = getDurationAndVariability(paths)
    #         dfScalar = pd.DataFrame({'variance':totVars,'session time (s)':totTimes,'fileNames':fileNames} )
    #         x = dfScalar['session time (s)']
    #         y = dfScalar['variance']
    #         names = dfScalar['fileNames']
    #         fig = myScatter(x,y,xlab = 'session time (s)' ,ylab = 'variance',names = names)  #px.scatter(dfScalar,x='session time (s)', y='variance', marginal_x="histogram", marginal_y="histogram",hover_data=['fileNames'])
    #         fig.add_shape(type="rect",
    #             x0=x_filter[0], y0=y_filter[0], x1=x_filter[1], y1=y_filter[1],
    #             line=dict(
    #                 color="RoyalBlue",
    #                 width=2,
    #             ),
    #             fillcolor="LightSkyBlue",
    #             layer="below",
    #         )
            
    #         xmin = np.floor(x.min()) 
    #         xmax = np.ceil(x.max())
    #         ymin = np.floor(y.min()) 
    #         ymax = np.ceil(y.max())

    #         return fig, str(x_filter), xmin, xmax, {xmin: str(xmin), xmax: str(xmax)}, str(y_filter), ymin, ymax, {ymin: str(ymin), ymax: str(ymax)}
    #     else:
    #         fig = myScatterEmpty(xlab = 'session time (s)' ,ylab = 'variance')
    #         return fig, str(x_filter), 0.0, 360.0, {0: '0', 360.: '360'}, str(y_filter), 0.0, 2.0, {0: '0.0', 2.: '2.0'}

    # @app.callback(
    #     Output("preprocessed-gated-record-names", "children"),
    #     Input("variables", "data"),
    # )
    # def get_saved_preprocessed_gated_record_names(data):
    #     data = json.loads(data) 
    #     project_name = data["project_name"]
    #     group_name = data["group_name"]
    #     print(group_name)
    #     if isinstance(group_name, str):#project_name in allowedProjects: 
    #         #fileNames, dfSs  = loadData(group_name,project_name,version='preprocessed-VR-sessions')
    #         records = projObj.get_recods_in_project_and_group(project_name,group_name,step='proc',version='preprocessed-VR-sessions-gated')
    #         fileNames = [re.name for re in records]
            
    #         return str(fileNames)
    #     else:
    #         return str(None)
        
    # @app.callback(
    #     Output("preprocessed-gated-selected-record-names", "children"),
    #     State("variables", "data"),
    #     Input("x-slider-output", "children"),
    #     Input("y-slider-output", "children"),
    # )
    # def get_selected_preprocessed_gated_record_names(data,xRange,yRange):
    #     data = json.loads(data) 
    #     project_name = data["project_name"]
    #     group_name = data["group_name"]
    #     print(group_name)
    #     thTime0,thTime1 = json.loads(xRange)
    #     thVar0,thVar1 = json.loads(yRange)
    #     print('xRange',json.loads(xRange),thTime0,thTime1)
    #     print('yRange',yRange)
    #     if isinstance(group_name, str):#project_name in allowedProjects: 
    #         #fileNames, dfSs  = loadData(group_name,project_name,version='preprocessed-VR-sessions')
    #         records = projObj.get_recods_in_project_and_group(project_name,group_name,step='proc',version='preprocessed-VR-sessions')
    #         fileNames = [re.name for re in records]
    #         print('file names',fileNames)
    #         dfSs = [re.data for re in records]
    #         paths = getPaths(dfSs)
    #         totTimes,totVars = getDurationAndVariability(paths)
    #         ungatedFileNames = []

    #         for fName,totVar,totTime in zip(fileNames, totVars, totTimes):
    #             #print('fName',fName)
    #             if (totVar >= thVar0) and (totVar <= thVar1) and (totTime >= thTime0) and (totTime <= thTime1):
    #                 ungatedFileNames.append(fName)
    #                 print('session in ',fName)
    #                 #assert session in d['preprocessedVRsessions'], "session not in preprocessedVRsessions "+session
    #                 #d['preprocessedVRsessions-gated'][session] = d['preprocessedVRsessions'][session]
    #                 #if 'ID' in dfS.columns: dfS = dfS.drop(columns=['ID', 'filename'])
    #                 #dfS.to_csv(gatedPath+'/'+session+'-preprocessed.csv',index=False,na_rep='NA')
    #             else:
    #                 print('session out',fName)
    #                 #tsi.drawPath(path, dpath=None, BBox=None)
    #         return json.dumps(ungatedFileNames)
    #     else:
    #         return json.dumps([])
        
    # @app.callback(
    #     #Output('container-button-basic', 'children'),
    #     State('variables', 'data'),
    #     State("preprocessed-gated-selected-record-names", "children"),
    #     State("x-slider-output", "children"),
    #     State("y-slider-output", "children"),
    #     Input('save-gate', 'n_clicks'),
    #     prevent_initial_call=True
    # )
    # def save_selected_records(data, selected_rec_names,xRange,yRange, n_clicks):
    #     #print('n_clicks',n_clicks )
    #     #print('data',data )
    #     #print('selected_rec_names',selected_rec_names )
    #     selectedNames = json.loads(selected_rec_names)
    #     #print('selected_rec_names',selectedNames )
    #     thTime0,thTime1 = json.loads(xRange)
    #     thVar0,thVar1 = json.loads(yRange)

    #     if n_clicks>0:
    #         print("Save ",data)
    #         dff = json.loads(data) #= pd.read_json(data)
    #         project_name = dff['project_name']
    #         group_name = dff['group_name']
    #         pregatedGroup = projObj.get_group(project_name,group_name,'proc',version='preprocessed-VR-sessions')
    #         gatedGroup = projObj.get_group(project_name,group_name,'proc',version='preprocessed-VR-sessions-gated')
    #         gatedPath = pregatedGroup.path + '/preprocessed-VR-sessions-gated'
    #         print('gatedGroup.records',gatedGroup.records)
    #         for record in gatedGroup.records:
    #             os.remove(record.path)
    #             record_name = record.name
    #             print('record_name to remove',record_name)
    #             #projObj.remove_record(record)#,project_name,group_name,version='preprocessed-VR-sessions-gated')
    #             requests.delete(f"{FASTAPI_URL}/records/proc/{project_name}/{group_name}/{record_name}/{version}")


    #         d = {}
    #         if pregatedGroup.parsFileExists():
    #             d = pregatedGroup.loadPars()
    #         #print('ungatedGroup pars',ungatedGroup.path,ungatedGroup.pars_path) 
    #         #print('ungatedGroup pars',ungatedGroup.pars) 
    #         #print(d['preprocessedVRsessions'])
    #         d['gated'] = {'thVar >=':thVar0,'thVar <=':thVar1,'thTime >=':thTime0,'thTime <=':thTime1}
    #         d['preprocessedVRsessions-gated'] = {}
    #         #print('d',d)

    #         for fName in selectedNames:
    #             print('fName',fName)
    #             #record =projObj.get_record(project_name,group_name,fName,'proc',version='preprocessed-VR-sessions')
    #             version='preprocessed-VR-sessions'
    #             records = requests.get(f"{FASTAPI_URL}/records/proc/{project_name}/{group_name}?ver={version}")
    #             record = [r for r in records.json() if r["name"] == file][0]

    #             #pathSes = record.group.path
    #             record_path = os.path.join(gatedPath,fName+'.csv')
    #             print('record',record.name)#,pathSes)

    #             # i = len(utils.records) + 1
    #             # ungatedRecord = Record(i, fName, record_path, 'proc', record.data) 
    #             # ungatedRecord.set_ver('preprocessed-VR-sessions-gated')
    #             # ungatedRecord.group = ungatedGroup
    #             # ungatedRecord.project = ungatedGroup.project
    #             # ungatedGroup.add_record(ungatedRecord)
    #             # ungatedRecord.parent_record = record
    #             # record.add_child_record(ungatedRecord)
    #             # utils.records.append(ungatedRecord)
    #             #ungatedRecord = projObj.add_record(record,gatedGroup,fName,record_path, record.data, version='preprocessed-VR-sessions-gated')
    #             ungatedRecords = requests.put(f"{FASTAPI_URL}/records/proc/{project_name}/{group_name}/{record_name}/{version}")
    #             ungatedRecord = [r for r in records.json() if r["name"] == file][0]
    #             d['preprocessedVRsessions-gated'][fName] = d['preprocessedVRsessions'][fName]

    #             ungatedRecord.data.to_csv(record_path,index=False,na_rep='NA')

    #         tsi.writeJson(pregatedGroup.pars_path,d)


    pass