import dash
#import dash_bootstrap_components as dbc
from dash import Dash, html, dcc, Output, Input, State

#from dash_apps import records_proc, group_proc

import requests

import json

FASTAPI_URL = "http://localhost:8000/api"



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



def init_callback_vars(app):
    app.callback(
        Output("project-name", "children"),
        Output("group-name", "children"),
        Output("record-name", "children"),
        Input('url', 'pathname'),
    )(update_variable)
    app.callback(
        Output("variables", "data"),  
        Input('url', 'pathname'),
    )(update_group_variables)
#    app.callback(
#        Output('page-content', 'children'),
#        Input('url', 'pathname')
#    )(display_page)
    
def init_callbacks(app):
    init_callback_vars(app)

    #records_proc.init_callbacks_records_proc(app)
    #group_proc.init_callbacks_group_proc(app)

    #By default, Dash applies validation to your callbacks, which performs checks such as validating the types of callback arguments and checking to see whether the specified Input and Output components actually have the specified properties.
    #app.config.suppress_callback_exceptions = True


# If initializing Dash app using Flask app as host
#app = Dash(server=g.cur_app, url_base_pathname=url_path)
dash_app = dash.Dash(__name__, requests_pathname_prefix='/vars/')#,  external_stylesheets=[dbc.themes.BOOTSTRAP]  )

# End if

# If initializing Dash app for middleware
#app = Dash(requests_pathname_prefix=url_path)

# End if

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
        html.Div(id='page-content'),
        dcc.Store(id='variables'),
])

#group_proc.init_app_group_proc(projObj)
#records_proc.init_app_records_proc(projObj)
init_callbacks(dash_app)
#return app.server



if __name__ == "__main__":
    dash_app.run(debug=True)