# quickbrowser.py
from google_cloud import gdatastore_results_to_df, gcloud_read_experiment
import appfunctions as af
import json
import dash
from dash import dcc
from dash.dependencies import Input, Output
from dash import html
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]
app = dash.Dash(
    __name__, external_stylesheets=external_stylesheets, title="LESO results browser"
)
server = app.server

options_dict = {
    "Low DC ratio": "low_dc",
    "High DC ratio": "high_dc",
    "Both DC ratio's": "both_dc",
}

COLLECTION = "cablepooling_paper"

app.layout = html.Div(
    [
        html.H3("Thesis Seth van Wieringen - Results analysis"),
        html.Div(
            [
                dcc.RangeSlider(),
                html.Div(),
                html.Div(),
                dcc.RangeSlider(min=1, max=2),
            ],
            style={"display": "grid", "grid-template-columns": r"90% 10%"},
        ),
        html.P("Select a simulation run"),
        dcc.Store(
            id="google-datastore-cache",
            data=gdatastore_results_to_df(collection=COLLECTION).to_json(),
        ),
    ],
    className="container",
)


if __name__ == "__main__":
    # app.run_server(host='0.0.0.0', port=8081, debug=True, use_reloader=False)
    app.run_server(debug=True)
