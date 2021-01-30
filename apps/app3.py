import dash
import dash_html_components as html
import dash_table
import pandas as pd
from app import app

#### GET DATA

dfAPI = pd.read_csv("freqs_data.csv")

#### LAYOUT

layout = html.Div(
    [
        html.H6(children="All records"),
        html.Div(
            [
                dash_table.DataTable(
                    id="table2",
                    data=dfAPI.round(2).to_dict("records"),
                    columns=[
                        {"id": c, "name": c}
                        for c in [
                            # "data point",
                            "ref#",
                            "text type",
                            "value",
                            "freq",
                            "fpm",
                            "rel",
                        ]
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
