import dash
import dash_html_components as html
import dash_core_components as dcc
import dash_table
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# import numpy as np
import re
from app import app

#### GET DATA

# load
ttypes = pd.read_csv("data/ttypes.csv")
ws = pd.read_csv("data/ws_freqs.csv")

DDtext_types = ["User"]

wsGRAPH = ws.loc[(ws["text type"].isin(DDtext_types))]  # .sort_values(by="frq")

fig = px.bar(
    wsGRAPH,
    x="fpm",
    y="word",
    color="value",
    orientation="h",
    title="Title",
)
# fig = go.Figure(go.Bar(x=wsGRAPH["frq"], y=wsGRAPH["word"],orientation="h"))

fig.update_layout(
    barmode="stack",
    yaxis={"categoryorder": "sum ascending"},
    width=1500,
    height=5000,
)


#### LAYOUT

layout = html.Div(
    [
        html.H6(children="Text type data"),
        html.Div([dcc.Graph(figure=fig)]),
        html.Div(
            [
                dash_table.DataTable(
                    id="table2",
                    data=ttypes.round(2).to_dict("records"),
                    columns=[{"id": c, "name": c} for c in ttypes.columns],
                    sort_action="native",
                    sort_mode="single",
                    filter_action="native",
                    page_action="native",
                    page_size=100,
                    style_table={
                        "overflowX": "scroll",
                        "maxHeight": "800px",
                        "overflowY": "scroll",
                    },
                    style_data={"whiteSpace": "normal", "height": "auto"},
                    style_cell={
                        "minWidth": "70px",
                        "maxWidth": "130px",
                        "overflow": "hidden",
                        "textOverflow": "ellipsis",
                    },
                    style_cell_conditional=[
                        {"if": {"column_id": "text type"}, "textAlign": "left"},
                        {"if": {"column_id": "value"}, "textAlign": "left"},
                        {"if": {"column_id": "ref#"}, "textAlign": "center"},
                    ],
                )
            ],
            style={"width": "100%"},
        ),
    ]
)
