import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.express as px
from colour import Color
import pandas as pd
from app import app

#### GET DATA

dfAPI = pd.read_csv("data/freqs_data.csv")
dfSTATSrels = pd.read_csv("data/freqs_stats_rels.csv")
# dfSTATSttypes = pd.read_csv("data/freqs_stats_ttypes.csv")
# make dict for graph hover values (quicker than w/ dataframes)
dtGRAM = dfSTATSrels[["ref#", "relation", "cql"]].set_index("ref#").T.to_dict("list")
# get text types
text_types = sorted(dfAPI["text type"].unique())

#### MAKE FACETED GRAPH DATAFRAME
dfGRAPH = pd.DataFrame()
for x in ["fpm", "rel"]:
    dftemp = dfAPI
    dftemp["int"] = dftemp[x]
    dftemp["stat"] = x
    dfGRAPH = dfGRAPH.append(dftemp, ignore_index=True)
dfGRAPH.drop(columns=["rel", "fpm"], inplace=True)

#### GET CQL INDEXES GROUPED BY RELATION
with open("grammar.txt") as f:
    lines = [line.rstrip() for line in f]
lines = lines[lines.index("### Pilar's relations start here") :]
# get indexes of CQL lines
cqllines = [i for i, x in enumerate(lines) if "[" in x]
# get indexes of relations
rel_lines = [i for i, x in enumerate(lines) if '="%w"' in x]
rel_names = [lines[i] for i in rel_lines]
rel_names = [i.replace("=", "") for i in rel_names]
rel_names = [i.replace('"%w"', "") for i in rel_names]
rel_names = [i.replace(".../ ", " / ") for i in rel_names]
rel_names = [i.replace("...", "") for i in rel_names]
# make dict of ref# by relation type
rel_list = {}
for i in range(0, len(rel_lines) - 1):
    rel_list[i] = [x for x in cqllines if x in range(rel_lines[i], rel_lines[i + 1])]
rel_list[len(rel_lines) - 1] = [
    x for x in cqllines if x in range(rel_lines[-1], len(lines))
]

#### MAKE CONTINUOUS COLOR SCALE
# https://www.w3schools.com/colors/colors_picker.asp using the lighter/darker scale values at 90% (lightest) and 10% (darkest)
colorRanges = [
    [Color("#ccccff"), Color("#000033")],  # blue
    [Color("#ffccff"), Color("#330033")],  # pink
    [Color("#ccffdd"), Color("#003311")],  # green
    [Color("#fff2cc"), Color("#332600")],  # yellow
    [Color("#ccffff"), Color("#003333")],  # turquoise
]
dtCOLORS = {}
for x in range(0, len(rel_list)):
    colorlist = list(colorRanges[x][0].range_to(colorRanges[x][1], len(rel_list[x])))
    dttemp = {
        dtGRAM[rel_list[x][y]][0]: str(colorlist[y]) for y in range(0, len(rel_list[x]))
    }
    dtCOLORS = {**dtCOLORS, **dttemp}

#### LAYOUT

layout = html.Div(
    children=[
        html.Div(
            [
                html.P(children="Text type", style={"width": "100px"}),
                dcc.Dropdown(
                    id="DDtext_types",
                    options=[{"label": i, "value": i} for i in text_types],
                    # value=["Genre"],
                    clearable=True,
                    multi=True,
                    style={"width": "100%"},
                ),
                html.Button("All", id="B_all_text_types", n_clicks=0),
            ],
            style={
                "display": "inline-flex",
                "width": "100%",
                "justify-content": "right",
            },
        ),
        html.Div(
            [
                html.P(children="Relation", style={"width": "100px"}),
                dcc.Dropdown(
                    id="DD_relation",
                    options=[
                        {"label": rel_names[i], "value": i}
                        for i in range(0, len(rel_names))
                    ],
                    # value=[0],
                    clearable=True,
                    multi=True,
                    style={"width": "100%"},
                ),
                html.Button("All", id="B_all_rels", n_clicks=0),
            ],
            style={
                "display": "inline-flex",
                "width": "100%",
                "justify-content": "right",
            },
        ),
        html.Div(
            [
                html.P("Colors", style={"width": "80px"}),
                dcc.RadioItems(
                    id="RAD_colors",
                    options=[
                        {"label": "continuous", "value": "cont"},
                        {"label": "discrete", "value": "disc"},
                    ],
                    value="cont",
                    labelStyle={"display": "inline-block"},
                ),
            ],
            style={
                "display": "inline-flex",
                "width": "100%",
                "justify-content": "left",
            },
        ),
        html.Div([dcc.Graph(id="graph1")]),
    ]
)

#### CALLBACKS


@app.callback(
    dash.dependencies.Output("graph1", "figure"),
    [
        dash.dependencies.Input("DDtext_types", "value"),
        dash.dependencies.Input("DD_relation", "value"),
        dash.dependencies.Input("RAD_colors", "value"),
    ],
)
def update_graph(DDtext_types, DD_relation, RAD_colors):
    rel_all = [rel_list[x] for x in DD_relation]
    rel_all = [i for s in rel_all for i in s]
    # filter by text type and relation
    dffAPI = dfGRAPH.loc[
        (dfGRAPH["ref#"].isin(rel_all)) & (dfGRAPH["text type"].isin(DDtext_types))
    ].sort_values(by="ref#")
    try:
        # graph
        fig = px.scatter()
        activeRels = [dtGRAM[x][0] for x in dffAPI["ref#"]]
        discrete = {x: dtCOLORS[x] for x in set(activeRels)}
        # color types
        if RAD_colors == "cont":
            fig = px.bar(
                dffAPI,
                x="int",
                y="value",
                orientation="h",
                color=activeRels,
                color_discrete_map=discrete,
                facet_col="stat",
            )
        else:
            fig = px.bar(
                dffAPI,
                x="int",
                y="value",
                orientation="h",
                color=activeRels,
                color_discrete_sequence=px.colors.qualitative.Dark24,
                facet_col="stat",
            )
        fig.update_xaxes(matches=None, title="")
        fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
        fig.update_layout(
            yaxis={"categoryorder": "category descending", "title": ""},
            height=max([250, len(dffAPI["value"].unique()) * 35]),
            # width=1000,
            legend_title="Pattern",
            legend=dict(itemclick="toggleothers", itemdoubleclick="toggle"),
        )
    except:
        fig = px.scatter()
    return fig


@app.callback(
    dash.dependencies.Output("DDtext_types", "value"),
    [dash.dependencies.Input("B_all_text_types", "n_clicks")],
)
def all_ttypes(n_clicks):
    if n_clicks == 0:
        return []
    return text_types


@app.callback(
    dash.dependencies.Output("DD_relation", "value"),
    [dash.dependencies.Input("B_all_rels", "n_clicks")],
)
def all_rels(n_clicks):
    if n_clicks == 0:
        return []
    return [x for x in range(0, len(rel_names))]
