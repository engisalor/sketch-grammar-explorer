import base64
import io
import pandas as pd
import pathlib
import json

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from flask_caching import Cache

from app import app
import scripts.classes as classes

cache = Cache(
    app.server,
    config={
        "CACHE_TYPE": "redis",
        "CACHE_TYPE": "filesystem",
        "CACHE_DIR": ".cache",
        "CACHE_DEFAULT_TIMEOUT": 0,
    },
)

#### LAYOUT

layout = html.Div(
    [
        dcc.Store(id="store_IDs", storage_type="session"),
        html.H5("Multi-call"),
        html.Div(
            [
                html.Button("Submit", id="submit", n_clicks=0),
                html.Button("Clear cache", id="clear_cache", n_clicks=0),
            ],
            style={
                "display": "flex",
                "flex-wrap": "wrap",
                "justify-content": "left",
                "align-items": "center",
            },
        ),
        dcc.Textarea(
            id="calls_input",
            persistence=True,
            persistence_type="session",
            placeholder=r""""q": ["alemma,\"ice\""], "refs": "doc,s", "corpname": "preloaded/ecolexicon_en", "viewmode": "sen", "pagesize": 20, "fromp": 1
"fromp":2
""",
            style={
                "display": "inline-flex",
                "width": "100%",
                "height": "150px",
            },
        ),
        html.Div(
            [
                html.H5("Cache"),
                dash_table.DataTable(
                    id="cacheTable",
                    data=pd.DataFrame().to_dict("records"),
                    columns=[],
                    # export_format='csv',
                    # export_headers='names',
                    merge_duplicate_headers=True,
                    sort_action="native",
                    sort_mode="single",
                    filter_action="native",
                    # row_deletable=True, # conflicts with filter_action
                    page_action="native",
                    page_size=100,
                    style_table={
                        "maxHeight": "200px",
                        "overflowY": "scroll",
                    },
                    style_data={"whiteSpace": "normal", "height": "auto"},
                    style_cell={"textAlign": "left", "padding": "5px"},
                    style_cell_conditional=[
                        {"if": {"column_id": "concsize"}, "textAlign": "right"}
                    ],
                    style_as_list_view=True,
                    style_header={"backgroundColor": "white", "fontWeight": "bold"},
                ),
                html.H5("Results"),
                html.Div([
                        html.Button('Add column', id='newColumn', n_clicks=0),
                    ]),
                dash_table.DataTable(
                    id="resultsTable",
                    data=pd.DataFrame().to_dict("records"),
                    columns=[],
                    merge_duplicate_headers=True,
                    filter_action="custom",
                    filter_query="",
                    sort_action="custom",
                    sort_mode="single",  # 'multi'
                    sort_by=[],
                    page_action="custom",
                    page_current=0,
                    page_size=500,
                    style_table={
                        "overflowX": "scroll",
                        "maxHeight": "800px",
                        "overflowY": "scroll",
                    },
                    style_data={"whiteSpace": "normal", "height": "auto"},
                    style_cell={"textAlign": "left", "padding": "5px"},
                    style_as_list_view=True,
                    style_header={"backgroundColor": "white", "fontWeight": "bold"},
                    style_cell_conditional=[
                        {"if": {"column_id": c}, "textAlign": "right"}
                        for c in [
                            "#",
                            "fromp",
                            "hit",
                        ]  # FIXME (maybe overridden by md formatting?)
                    ],
                ),
            ],
            # style={},
        ),
    ],
    style={"margin": "10px"},
)


# submit API call
@app.callback(
    Output("store_IDs", "data"),
    [Input("submit", "n_clicks"), Input("clear_cache", "n_clicks")],
    [State("calls_input", "value")],
    prevent_initial_call=False,
)
def submitcall(submitclicks, clearclicks, calls_input):
    # get button_id
    ctx = dash.callback_context
    if not ctx.triggered:
        button_id = None
    else:
        button_id = ctx.triggered[0]["prop_id"].split(".")[0]

    # get cached
    cache_IDs = cache.get("ledger")
    if cache_IDs is None:
        cache_IDs = []

    # do call
    if button_id == "submit":
        call_data = getattr(classes, "view")(calls_input=calls_input)
        call_data.make_calls(cache=cache, cache_IDs=cache_IDs)
        cache_IDs.extend(call_data.IDs)

    # clear cache:
    if button_id == "clear_cache":
        if 0 < clearclicks:
            cache.clear()
            cache_IDs = None
    cache.set("ledger", cache_IDs)

    return cache_IDs


# Python-driven filtering
operators = [
    ["ge ", ">="],
    ["le ", "<="],
    ["lt ", "<"],
    ["gt ", ">"],
    ["ne ", "!="],
    ["eq ", "="],
    ["contains "],
    ["datestartswith "],
]


def split_filter_part(filter_part):
    for operator_type in operators:
        for operator in operator_type:
            if operator in filter_part:
                name_part, value_part = filter_part.split(operator, 1)
                name = name_part[name_part.find("{") + 1 : name_part.rfind("}")]

                value_part = value_part.strip()
                v0 = value_part[0]
                if v0 == value_part[-1] and v0 in ("'", '"', "`"):
                    value = value_part[1:-1].replace("\\" + v0, v0)
                else:
                    try:
                        value = float(value_part)
                    except ValueError:
                        value = value_part

                # word operators need spaces after them in the filter string,
                # but we don't want these later
                return name, operator_type[0].strip(), value
    return [None] * 3


# make results table
@app.callback(
    [
        Output("resultsTable", "data"),
        Output("resultsTable", "columns"),
        Output("resultsTable", "page_count"),
    ],
    [
        Input("store_IDs", "data"),
        Input("resultsTable", "page_size"),
        Input("resultsTable", "page_current"),
        Input("resultsTable", "sort_by"),
        Input("resultsTable", "filter_query"),
    ],
)
def updatetable(trigger, page_size, page_current, sort_by, filter_query):
    # get cached data
    dff = cache.get("results_df")
    if dff is None:
        dff = pd.DataFrame()
    dff["#"] = range(len(dff))

    # filtering
    filtering_expressions = filter_query.split(" && ")
    for filter_part in filtering_expressions:
        col_name, operator, filter_value = split_filter_part(filter_part)
        if operator in ("eq", "ne", "lt", "le", "gt", "ge"):
            # these operators match pandas series operator method names
            dff = dff.loc[getattr(dff[col_name], operator)(filter_value)]
        elif operator == "contains":
            dff = dff.loc[dff[col_name].str.contains(filter_value)]
        elif operator == "datestartswith":
            # this is a simplification of the front-end filtering logic,
            # only works with complete fields in standard format
            dff = dff.loc[dff[col_name].str.startswith(filter_value)]

    # sorting
    if len(sort_by):
        dff = dff.sort_values(
            [col["column_id"] for col in sort_by],
            ascending=[col["direction"] == "asc" for col in sort_by],
            inplace=False,
        )

    # get page_count
    cache_IDs = cache.get("ledger")
    if cache_IDs is not None:
        rows = sum([x["length"][0] for x in cache_IDs])
        page_count = rows // page_size + (rows % page_size > 0)
    elif filter_query:
        page_count = len(dff) // page_size + (len(dff) % page_size > 0)
    else:
        page_count = 0

    columns = [
        {"name": i, "id": i, "presentation": "markdown"}
        for i in dff.columns
        if i not in ["hash"]
    ]
    return (
        dff.iloc[page_current * page_size : (page_current + 1) * page_size].to_dict(
            "records"
        ),
        columns,
        page_count,
    )


# make cache table
@app.callback(
    [Output("cacheTable", "data"), Output("cacheTable", "columns")],
    [Input("store_IDs", "data")],
)
def cacheTable(trigger):
    cache_IDs = cache.get("ledger")
    if cache_IDs is None or len(cache_IDs) == 0:
        return [], []
    else:
        return cache_IDs, [
            {"name": i, "id": i} for i in cache_IDs[0].keys() if i not in ["hash"]
        ]
