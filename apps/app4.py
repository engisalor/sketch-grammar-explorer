import dash
import dash_html_components as html
import dash_table
import pandas as pd
#import numpy as np
import re
from app import app

#### GET DATA

# load
temp = pd.read_csv('data/ttypes.csv')

#### LAYOUT

layout = html.Div(
    [
        html.H6(children="Text type data"),
        html.Div(
            [
                dash_table.DataTable(
                    id="table2",
                    data=temp.round(2).to_dict("records"),
                    columns=[
                        {"id": c, "name": c}
                        for c in temp.columns
                    ],
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
