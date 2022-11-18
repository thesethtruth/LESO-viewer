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
options_dict = {
    "Low DC ratio": "low_dc",
    "High DC ratio": "high_dc",
    "Both DC ratio's": "both_dc",
}
COLLECTION = "cablepooling_paper"

app = dash.Dash(
    __name__, external_stylesheets=external_stylesheets, title="LESO results browser"
)
server = app.server

app.layout = html.Div(
    [
        html.H3("Cable pooling paper Emiel&Seth - Results analysis"),
        html.Div(
            [
                dcc.Markdown("Select the **experiment** dataset to explore:"),
                dcc.Markdown(""),
                dcc.Dropdown(
                    id="experiment-select",
                    persistence=True,
                    options=[
                        {"label": key, "value": value}
                        for key, value in options_dict.items()
                    ],
                    value=list(options_dict.values())[0],
                ),
                dcc.Markdown(""),
                dcc.Markdown("Select a **primary** feature to filter:"),
                dcc.Markdown("Select a **secondary** feature to filter:"),
                dcc.Dropdown(
                    id="filter-select-A",
                    persistence=True,
                ),
                dcc.Dropdown(
                    id="filter-select-B",
                    persistence=True,
                ),
                dcc.Markdown("Select the **hue** feature to use:"),
                dcc.Markdown("Select the **size** feature to use:"),
                dcc.Dropdown(
                    id="hue-select",
                    persistence=True,
                ),
                dcc.Dropdown(
                    id="size-select",
                    persistence=True,
                ),
            ],
            style={
                "display": "grid",
                "grid-template-columns": r"50% 50%",
                "grid-template-rows": "auto",
            },
        ),
        html.Div(
            [
                dcc.RangeSlider(
                    min=1,
                    max=2,
                    id="filter-slider-A",
                    persistence=True,
                    className="topslider",
                ),
                html.Div(),
                dcc.Graph(id="filter-fig", config={"displayModeBar": False}),
                dcc.RangeSlider(
                    min=1,
                    max=2,
                    id="filter-slider-B",
                    vertical=True,
                    verticalHeight=355,
                    className="rightslider",
                ),
            ],
            style={"display": "grid", "grid-template-columns": r"90% 10%"},
        ),
        html.P("Select a simulation run"),
        dcc.Dropdown(
            id="filtered-experiment-select",
            persistence=True,
        ),
        dcc.Graph(id="hourly"),
        html.P(
            ["Browse through the year per weeknumber below:"],
            style={"padding-left": "5%"},
        ),
        dcc.Slider(
            id="startingweek",
            min=min(af.weeks.values()),
            max=max(af.weeks.values()),
            step=1,
            value=af.startingweek,
            persistence=False,
        ),
        dcc.Store(
            id="google-datastore-cache",
            data=gdatastore_results_to_df(collection=COLLECTION).to_json(),
        ),
        dcc.Store(
            id="filtered-google-datastore-cache",
            data=dict(),
        ),
        dcc.Store(
            id="timeseries-store",
            data=dict(),
        ),
        dcc.Store(
            id="store-filtered-df",
            data=dict(),
        ),
    ],
    className="container",
)

## filter-select-A/B populator


@app.callback(
    Output("filter-select-A", "options"),
    Output("filter-select-A", "value"),
    Output("filter-select-B", "options"),
    Output("filter-select-B", "value"),
    Output("hue-select", "options"),
    Output("hue-select", "value"),
    Output("size-select", "options"),
    Output("size-select", "value"),
    Input("google-datastore-cache", "data"),
)
def populate_dropdowns(data):
    df = pd.DataFrame.from_dict(json.loads(data))
    cols = [col for col in df.columns if df[col].dtype == "float64"]
    options = [{"label": key, "value": key} for key in cols]
    value = cols[0]

    x_default = "pv_cost"
    y_default = "battery_cost"
    hue_default = "curtailment"
    size_default = "PV low DC ratio installed capacity"

    return (
        options,
        x_default,
        options,
        y_default,
        options,
        hue_default,
        options,
        size_default,
    )


@app.callback(
    Output("filtered-google-datastore-cache", "data"),
    Input("experiment-select", "value"),
    Input("google-datastore-cache", "data"),
)
def filter_cached_datastore_df(experiment, data):

    df = pd.DataFrame.from_dict(json.loads(data))

    if experiment != "null":
        df = df.query(f"experiment == '{experiment}'")
    return df.to_json()


## reads associated JSON file and stores to react app
## (this allows for sharing between callbacks)
@app.callback(
    Output("timeseries-store", "data"),
    Input("filtered-experiment-select", "value"),
)
def data_store(experiment_id):

    if experiment_id is None:
        ...
    else:
        return gcloud_read_experiment(
            collection=COLLECTION, experiment_id=experiment_id
        )


## Filter A
@app.callback(
    Output("filter-slider-A", "min"),
    Output("filter-slider-A", "max"),
    Output("filter-slider-A", "value"),
    Output("filter-slider-A", "marks"),
    Output("filter-slider-A", "step"),
    Input("filter-select-A", "value"),
    Input("google-datastore-cache", "data"),
)
def filter_a(feature, data):
    df = pd.DataFrame.from_dict(json.loads(data))
    minn = df[feature].min()
    maxx = df[feature].max()
    value = [minn, maxx]
    marks = {str(i): "" for i in value}
    step = (maxx - minn) / 100
    return minn, maxx, value, marks, step


## Filter B
@app.callback(
    Output("filter-slider-B", "min"),
    Output("filter-slider-B", "max"),
    Output("filter-slider-B", "value"),
    Output("filter-slider-B", "marks"),
    Output("filter-slider-B", "step"),
    Input("filter-select-B", "value"),
    Input("google-datastore-cache", "data"),
)
def filter_a(feature, data):
    df = pd.DataFrame.from_dict(json.loads(data))
    minn = df[feature].min()
    maxx = df[feature].max()
    value = [minn, maxx]
    marks = {str(i): "" for i in value}
    step = (maxx - minn) / 100
    return minn, maxx, value, marks, step


# visualize the filter
@app.callback(
    Output("filter-fig", "figure"),
    Output("store-filtered-df", "data"),
    Input("filter-select-A", "value"),
    Input("filter-select-B", "value"),
    Input("filter-slider-A", "value"),
    Input("filter-slider-B", "value"),
    Input("filtered-google-datastore-cache", "data"),
    Input("hue-select", "value"),
    Input("size-select", "value"),
)
def filter_figure(x_col, y_col, x_range, y_range, data, hue, size):
    df = pd.DataFrame.from_dict(json.loads(data))
    xmin, xmax = x_range
    ymin, ymax = y_range
    if hue == "None":
        hue = None
    if size == "None":
        size = None

    x_slice = (df[x_col] >= xmin) & (df[x_col] <= xmax)
    y_slice = (df[y_col] >= ymin) & (df[y_col] <= ymax)
    total_slice = x_slice & y_slice
    sliced_df = df[total_slice]
    layout = go.Layout({"showlegend": False})
    fig = go.Figure(
        data=px.scatter(
            sliced_df,
            x=x_col,
            y=y_col,
            color=hue,
            size=size,
            custom_data=["filename_export"],
        ),
        layout=layout,
    )
    fig.update_traces(
        hovertemplate="<br>".join(
            [
                f"{x_col}: " + "%{x}",
                f"{y_col}: " + "%{y}",
                "Simulation run ID: %{customdata[0]}",
            ]
        )
    )
    fig.update_layout(
        template="simple_white",
        margin=dict(l=50, r=25, t=25, b=0),
        height=430,
        showlegend=False,
    )
    for trace in fig["data"]:
        trace["showlegend"] = False
    fig.update(layout_showlegend=False)
    fig.update_xaxes(range=(df[x_col].min() * 1.0, df[x_col].max() * 1.0))
    fig.update_yaxes(range=(df[y_col].min() * 1.0, df[y_col].max() * 1.0))

    data = sliced_df.to_json()
    return fig, data


## populate dropdown based on selection
@app.callback(
    Output("filtered-experiment-select", "options"),
    Output("filtered-experiment-select", "value"),
    Input("store-filtered-df", "data"),
)
def populate_filtered_experiments(data):

    df = pd.DataFrame.from_dict(json.loads(data))
    filenames_strs = df.filename_export

    options = [{"label": filename, "value": filename} for filename in filenames_strs]
    value = options[0]["value"]
    return options, value


## hourly profile plot
@app.callback(
    Output("hourly", "figure"),
    Input("startingweek", "value"),
    Input("timeseries-store", "data"),
)
def profile_plot(startingweek, data):
    fig = af.make_profile_plot(startingweek, data)

    return fig


if __name__ == "__main__":
    # app.run_server(host='0.0.0.0', port=8081, debug=True, use_reloader=False)
    app.run_server(debug=True)
