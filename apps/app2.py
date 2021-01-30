import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import pandas as pd
from app import app

#### GET DATA

dfSTATSrels = pd.read_csv("freqs_stats_rels.csv")
dfSTATSttypes = pd.read_csv("freqs_stats_ttypes.csv")

#### LAYOUT

layout = html.Div(
    [
        html.H6(children="Summary of frequency data"),
        html.Div(
            [
                dcc.RadioItems(
                    id="RADstat",
                    options=[
                        {"label": x, "value": x} for x in ["text type", "relation"]
                    ],
                    value="relation",
                    labelStyle={"display": "inline-block"},
                ),
                dcc.Checklist(
                    id="CHfreqs",
                    options=[
                        {"label": x, "value": x + " "} for x in ["freq", "fpm", "rel"]
                    ],
                    value=[
                        "freq ",
                        "fpm ",
                        "rel ",
                    ],  # trailing space is to avoid altering 'relation' column
                    labelStyle={"display": "inline-block"},
                ),
            ],
            style={
                "display": "inline-flex",
                "width": "100%",
                "justify-content": "right",
            },
        ),
        html.Div(
            dash_table.DataTable(
                id="table1",
                data=dfSTATSttypes.round(2).to_dict("records"),
                columns=[{"id": c, "name": c} for c in dfSTATSttypes.columns],
                sort_action="native",
                sort_mode="single",
                filter_action="native",
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
                    {"if": {"column_id": "relation"}, "textAlign": "left"},
                    {"if": {"column_id": "ref#"}, "textAlign": "center"},
                    {"if": {"column_id": "cql"}, "textAlign": "left"},
                ],
            )
        ),
    ],
    style={"width": "100%"},
)

#### CALLBACKS


@app.callback(
    [
        dash.dependencies.Output("table1", "data"),
        dash.dependencies.Output("table1", "columns"),
    ],
    [
        dash.dependencies.Input("CHfreqs", "value"),
        dash.dependencies.Input("RADstat", "value"),
    ],
)
def update_table(CHfreqs, RADstat):
    # get active stats table
    if RADstat == "text type":
        dfSTATS = dfSTATSttypes
        cols = [{"id": c, "name": c} for c in ["text type", "count"]]
    else:
        dfSTATS = dfSTATSrels
        cols = [
            {"id": c, "name": c}
            for c in ["ref#", "relation", "cql", "concsize", "count"]
        ]
    # maintain column order
    order = ["freq ", "fpm ", "rel "]
    CHfreqs = [{"o": x} for x in CHfreqs]
    sortCH = {key: i for i, key in enumerate(order)}
    CHfreqs = [x["o"] for x in sorted(CHfreqs, key=lambda d: sortCH[d["o"]])]
    # add active columns
    adds = []
    for x in CHfreqs:
        adds = adds + [col for col in dfSTATSrels if col.startswith(x)]
    cols = cols + [{"id": c, "name": c} for c in adds]

    return dfSTATS.round(2).to_dict("records"), cols
