import dash
#import dash_bootstrap_components as dbc
from dash_app.layout import layout_vars_app
from dash_app.callbacks import register_callback_vars


dash_app = dash.Dash(__name__, requests_pathname_prefix='/vars/')#,  external_stylesheets=[dbc.themes.BOOTSTRAP]  )


dash_app.layout =  layout_vars_app

#group_proc.init_app_group_proc(projObj)
#records_proc.init_app_records_proc(projObj)
register_callback_vars(dash_app)
#return app.server



if __name__ == "__main__":
    dash_app.run(debug=True)