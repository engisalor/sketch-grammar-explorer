import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
from dash.dependencies import Input, Output
import plotly.express as px
from colour import Color

# import requests
# import dash_auth
import pandas as pd

#### GET DATA
dfAPI = pd.read_csv("freqs_data.csv")
dfAPI["#"] = dfAPI.index
dfSTATSrels = pd.read_csv("freqs_stats_rels.csv")
dfSTATSttypes = pd.read_csv("freqs_stats_ttypes.csv")
# make dict for graph hover values (quicker than w/ dataframes)
dtGRAM = dfSTATSrels[["ref#", "relation", "cql"]].set_index("ref#").T.to_dict("list")
# exclude text types with too many values from graph
text_types = sorted(dfAPI["text type"].unique())
text_types = [x for x in text_types if x not in ["Author", "Title", "Keywords"]]
# TODO drop these data points from df before uploading to app


#### GENERATE DATAFRAME FOR FACETED GRAPH
dfNEW = pd.DataFrame()
for x in ["fpm", "rel"]:
    dftemp = dfAPI
    dftemp["int"] = dftemp[x]
    dftemp["stat"] = x
    dfNEW = dfNEW.append(dftemp, ignore_index=True)

dfNEW.sort_values(by="#").head()
dfNEW.drop(columns=["rel", "fpm"], inplace=True)

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
# make continuous color scales
# colors defined with https://www.w3schools.com/colors/colors_picker.asp using the lighter/darker scale values at 90% (lighest) and 10% (darkest)
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

#### APP
# get authentication pairs
# with open("auth_app.txt") as f:
#     VALID_USERNAME_PASSWORD_PAIRS = dict(x.rstrip().split(":") for x in f)
app = dash.Dash(__name__)
# app = dash.Dash(__name__, external_stylesheets=['https://codepen.io/chriddyp/pen/bWLwgP.css'])
server = app.server
# auth = dash_auth.BasicAuth(app, VALID_USERNAME_PASSWORD_PAIRS)
app.layout = html.Div(
    children=[
        html.Div(
            [
                html.Img(
                    src=app.get_asset_url("logo_ugr.png"),
                    # src='https://secretariageneral.ugr.es/pages/ivc/descarga/_img/horizontal/ugrmarca02color_2/!',
                    alt="University of Granada",
                    height=50,
                ),
                html.Div(
                    [
                        html.Div(
                            dcc.Link(
                                "LexiCon Research Group",
                                href="https://ecolexicon.ugr.es/",
                                target="blank",
                            )
                        ),
                        html.Div(
                            dcc.Link(
                                "Sketch Engine",
                                href="https://www.sketchengine.eu/",
                                target="blank",
                            )
                        ),
                        html.Div(
                            dcc.Link(
                                "Dash", href="https://plotly.com/dash/", target="blank"
                            )
                        ),
                    ]
                ),
            ],
            style={"display": "flex", "justify-content": "space-between"},
        ),
        html.H2(children="Sketch Grammar Explorer"),
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
        html.Div(
            [
                html.H6(children="Summary of frequency data"),
                html.Div(
                    [
                        dcc.RadioItems(
                            id="RADstat",
                            options=[
                                {"label": x, "value": x}
                                for x in ["text type", "relation"]
                            ],
                            value="text type",
                            labelStyle={"display": "inline-block"},
                        ),
                        dcc.Checklist(
                            id="CHfreqs",
                            options=[
                                {"label": x, "value": x + " "}
                                for x in ["freq", "fpm", "rel"]
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
                    [
                        dash_table.DataTable(
                            id="table1",
                            data=dfSTATSttypes.round(2).to_dict("records"),
                            columns=[
                                {"id": c, "name": c} for c in dfSTATSttypes.columns
                            ],
                            sort_action="native",
                            sort_mode="single",
                            filter_action="native",
                            style_table={
                                "overflowX": "scroll",
                                "maxHeight": "400px",
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
                    ],
                    style={"width": "100%"},
                ),
                html.Br(),
                html.H6(children="all records"),
                html.Div(
                    [
                        dash_table.DataTable(
                            id="table2",
                            data=dfAPI.round(2).to_dict("records"),
                            columns=[
                                {"id": c, "name": c}
                                for c in [
                                    "#",
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
                                "maxHeight": "400px",
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
                html.Div(
                    [
                        dcc.Markdown(
                            """
            > ###### Filter usage
            > * numbers: 
            >   * e.g. "79" (quotes required) 
            >   * results will include 79 & 23.79
            > * greater, lesser & equals signs:
            >   * e.g. >=64, !=author & <102
            >   * quotes usually optional
            > * text    
            >   * e.g. atmospheric sciences
            >   * quotes usually optional
                """
                        )
                    ],
                    style={
                        "display": "inline-flex",
                        "width": "100%",
                        "justify-content": "left",
                    },
                ),
            ]
        ),
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
    dffAPI = dfNEW.loc[
        (dfNEW["ref#"].isin(rel_all)) & (dfNEW["text type"].isin(DDtext_types))
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


if __name__ == "__main__":
    app.run_server(debug=True)
