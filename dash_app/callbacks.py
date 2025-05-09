from dash import Input, Output, State
import requests
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