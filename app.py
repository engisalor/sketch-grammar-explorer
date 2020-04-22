import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
from dash.dependencies import Input, Output
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import requests
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
text_types = [x for x in text_types if x not in ["author", "title", "keywords"]]


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
                html.Div(
                    [html.P(children="select text type")], style={"width": "250px"}
                ),
                html.Div([html.P("adjust figure height")], style={"width": "220px"}),
            ],
            style={
                "display": "inline-flex",
                "width": "100%",
                "justify-content": "right",
            },
        ),
        html.Div(
            [
                dcc.Dropdown(
                    id="DDtext_types",
                    options=[{"label": i, "value": i} for i in text_types],
                    value="genre",
                    clearable=False,
                    style={"width": "230px"},
                ),
                html.Div(
                    [
                        dcc.RangeSlider(
                            id="SLheight", min=200, max=1200, step=50, value=[600]
                        )
                    ],
                    style={"width": "250px"},
                ),
            ],
            style={
                "display": "inline-flex",
                "width": "100%",
                "justify-content": "right",
            },
        ),
        html.Div([dcc.Graph(id="graph1")]),
        html.Div(
            [
                html.H6(children="descriptive stats"),
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
                            ],  # space is to avoid altering 'relation' column
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
            > ###### filter usage
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
        dash.dependencies.Input("SLheight", "value"),
    ],
)
def update_graph(DDtext_types, SLheight):
    fig = make_subplots(
        rows=2,
        cols=1,
        # shared_xaxes=True,  # AVOID adds ghost columns
        vertical_spacing=0.03,
    )
    dffAPI = dfAPI.loc[dfAPI["text type"] == DDtext_types].sort_values(by="value")
    # add bar traces
    for i in dtGRAM.keys():
        value = dffAPI.loc[dffAPI["ref#"] == i]["value"]
        fig.add_trace(
            go.Bar(
                name="",
                legendgroup=i,
                x=value,
                y=dffAPI.loc[dffAPI["ref#"] == i]["rel"],
                text=["(" + str(i) + ") " + dtGRAM[i][0] for x in dffAPI["ref#"]],
                hovertemplate="<b>%{text}</b><br>"
                + "<b>value</b>: %{x}<br>"
                + "<b>rel</b>: %{y:.2f}<br>",
            ),
            row=2,
            col=1,
        )
        fig.add_trace(
            go.Bar(
                name="(" + str(i) + ")",
                legendgroup=i,
                x=value,
                y=dffAPI.loc[dffAPI["ref#"] == i]["fpm"],
                text=["(" + str(i) + ") " + dtGRAM[i][0] for x in dffAPI["ref#"]],
                customdata=dffAPI.loc[dffAPI["ref#"] == i]["freq"],
                hovertemplate="<b>%{text}</b><br>"
                + "<b>value</b>: %{x}<br>"
                + "<b>fpm</b>: %{y:.2f}<br>"
                + "<b>freq</b>: %{customdata}<br>",
            ),
            row=1,
            col=1,
        )
    # Update figure properties
    fig.update_layout(
        # xaxis={'categoryorder':'category ascending'},  # AVOID adds ghost columns
        height=SLheight[0],
        barmode="stack",
        title_text="<b>distribution by text type values<b>",
        legend_title="<b>relation</b>",
        legend=dict(itemclick="toggleothers", itemdoubleclick="toggle"),
    )
    fig.update_xaxes(showticklabels=False, row=1, col=1)
    fig.update_yaxes(title_text="<b>fpm</b>", row=1, col=1)
    fig.update_yaxes(title_text="<b>rel</b>", row=2, col=1)
    fig.update_xaxes(title_text="<b>" + DDtext_types + "</b>", row=2, col=1)

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


if __name__ == "__main__":
    app.run_server(debug=True)
