from dash import Input, Output, State

import requests
import json

import pandas as pd
import plotly.express as px

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

def register_callback_vars(app):
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