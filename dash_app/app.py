import dash

from dash_app.layout import layout
from dash_app.callbacks import register_callbacks



dash_app = dash.Dash(__name__, requests_pathname_prefix='/dashboard/')
dash_app.title = "Record Dash"
# dash_app.layout = layout

register_callbacks(dash_app)


# App layout
dash_app.layout = layout


