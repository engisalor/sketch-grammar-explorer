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

cache = Cache(app.server, config={
    'CACHE_TYPE': 'redis',
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR': '.cache',
    'CACHE_DEFAULT_TIMEOUT': 0,
})

# TODO #13 add metadata cols, make hidden

#### LAYOUT

layout = html.Div(
    [
        dcc.Store(id="cacheIDs", storage_type="session"),
        dcc.Store(id='params', storage_type='session'),
        dcc.Store(id='settings', storage_type='session'),
        html.H5("Multi-call"),
        html.Div([
        html.Button('Submit', id='submit', n_clicks=0),
        html.Button('Clear', id='clearcache', n_clicks=0),
        dcc.Dropdown(
            id="calltype",
            persistence=True,
            persistence_type="session",
            placeholder='query type',
            options=[
                {'label': 'view', 'value': 'view'},
                ],
            value="view",
            clearable=False,
            style={"width": "175px"},
            ),
        dcc.Dropdown(
            id="corpus",
            clearable=False,
            persistence=True,
            persistence_type="session",
            placeholder='corpus',
            options=[
                {'label': 'ecolexicon_en', 'value': 'preloaded/ecolexicon_en'},
                ],
            value="preloaded/ecolexicon_en",
            style={"width": "175px"},
        ),  
        dcc.Dropdown(
            id='qattr',
            persistence=True,
            persistence_type="session",
            clearable=False,
            placeholder='default attribute',
            value='alemma,',
            options=[
                {'label': 'lemma', 'value': 'alemma,'},
                {'label': 'word', 'value': 'aword,'},
                {'label': 'tag', 'value': 'atag,'},
                {'label': 'lempos', 'value': 'alempos,'},
                {'label': 'lempos_lc', 'value': 'alempos_lc,'},
                {'label': 'lemma_lc', 'value': 'alemma_lc,'},
                {'label': 'word_lc', 'value': 'aword_lc,'},
            ],
            style={"width": "175px"},
            ),
        dcc.Dropdown(
            id="viewmode",
            persistence=True,
            persistence_type="session",
            clearable=False,
            placeholder='view mode',
            options=[
                {'label': 'sentence', 'value': 'sen'},
                {'label': 'KWIC', 'value': 'kwic'}],
            value='sen',
            style={"width": "175px"},
        ),  
        dcc.Input(
            id="randomize",
            persistence=True,
            persistence_type="session",
            type="text",
            placeholder='random: r500 / r10%',
            value='',
            style={"width": "175px"},
        ),
        dcc.Input(
            id="pagesize",
            persistence=True,
            persistence_type="session",
            type="number",
            placeholder="size",
            value=20,
            min=1,
            max=10000,
            style={"width": "80px"},
        ),
        dcc.Input(
            id="refs",
            persistence=True,
            persistence_type="session",
            value="doc,s",
            placeholder='refs',
            style={"flex-grow": "1"},
        )],
        style={
            "display": "flex",
            "flex-wrap": "wrap",
            "justify-content": "left",
            "align-items":"center",
            },
        ),
        dcc.Textarea(
            id="clist",
            persistence=True,
            persistence_type="session",
            placeholder=r""""q:" ''' "water" ''' 
"fromp": 2
""",
            style={
                "display": "inline-flex",
                "width": "100%",
                "height": "150px",
                }), 
        # html.Div([
#         dcc.Loading(
#         id="loading",
#         children=[html.Div([html.Div(id="loading_output")])],
#         type="circle")],
#             style={
#                 "display": "inline-flex",
#                 "width": "100%",
#                 "justify-content": "space-around",
#             },
# ),
    #     dcc.Upload(
    #     id='upload',
    #     children=html.Div([
    #         'Drag and Drop or ',
    #         html.A('Select Files')
    #     ]),
    #     style={
    #         'width': '250px', 'height': '30px', 'lineHeight': '30px',
    #         'borderWidth': '1px', 'borderStyle': 'dashed',
    #         'borderRadius': '5px', 'textAlign': 'center', 'margin': '10px'
    #     },
    # ),
        html.Div(
            [
                html.H5("Cache"),
                dash_table.DataTable(
                    id="cacheTable",
                    data=pd.DataFrame().to_dict("records"),
                    columns=[],
                    export_format='csv',
                    export_headers='names',
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
                    style_cell={'textAlign': 'left','padding': '5px'}, 
                    style_cell_conditional=[
                        {
                            'if': {'column_id': 'concsize'},
                            'textAlign': 'right'
                        }
                    ],
                    style_as_list_view=True,
                    style_header={
                        'backgroundColor': 'white',
                        'fontWeight': 'bold'
                    },
                    ),
                html.H5("Results"),
                dash_table.DataTable(
                    id="resultsTable",
                    data=pd.DataFrame().to_dict("records"),
                    columns=[],
                    export_format='csv',
                    export_headers='names',
                    merge_duplicate_headers=True,
                    sort_action="native",
                    sort_mode="single",
                    filter_action="native",
                    page_action="native",
                    page_size=500,
                    style_table={
                        "overflowX": "scroll",
                        "maxHeight": "800px",
                        "overflowY": "scroll",
                    },
                    style_data={"whiteSpace": "normal", "height": "auto"},
                    style_cell={'textAlign': 'left','padding': '5px'}, 
                    style_as_list_view=True,
                    style_header={
                        'backgroundColor': 'white',
                        'fontWeight': 'bold'
                    },
                    style_cell_conditional=[
                        {
                            'if': {'column_id': c},
                            'textAlign': 'right'
                        } for c in ["#","fromp","hit"] # FIXME (maybe overridden by md formatting?)
                    ],
                )
            ],
            # style={},
        ),
    ], style={'margin': '10px'},
)

#### CALLBACKS

# for uploading files
def parse_contents(contents, filename):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    if 'csv' in filename:
        # Assume that the user uploaded a CSV file
        return pd.read_csv(
            io.StringIO(decoded.decode('utf-8')))
    elif 'xls' in filename:
        # Assume that the user uploaded an excel file
        return pd.read_excel(io.BytesIO(decoded))

# get params
@app.callback(Output("params", "data"),
    [Input("refs","value"),
    Input("corpus","value"),
    Input("viewmode","value"),
    Input("pagesize", "value")])
def params(refs,corpus,viewmode,pagesize):
    params = {
        "corpname": corpus, 
        "viewmode": viewmode,
        "pagesize": pagesize, 
        "fromp": 1}
    if refs:
        params["refs"] = refs
    return params

# get settings
@app.callback(Output("settings", "data"),
    [Input("calltype","value"),
    Input("qattr","value"),
    Input("randomize","value")])
def settings(calltype,qattr,randomize):
    settings = {
        "calltype": calltype,
        "qattr": qattr, 
        "randomize": randomize}
    return settings

# submit API call
@app.callback(Output("cacheIDs","data"),
    [Input("submit", "n_clicks"),
    Input("clearcache", "n_clicks")],
    [State("params","data"),
    State("settings","data"),
    State("clist","value")],
    prevent_initial_call=False)
def submitcall(submitclicks,clearclicks,params,settings,clist):
    # set button_id
    ctx = dash.callback_context
    if not ctx.triggered:
        button_id = None
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    # get cached
    cacheIDs = cache.get("ledger")
    # do call
    if button_id == "submit":
        # make instance
        c = getattr(classes,settings["calltype"])(params,settings,clist)
        # do calls
        cacheIDs = c.makecalls(cache=cache,cacheIDs=cacheIDs) # TODO add labels, etc., to cacheIDs
    # clear cache:
    if button_id == "clearcache":
        if 0 < clearclicks:
            cache.clear()
            cacheIDs = None
    cache.set("ledger", cacheIDs)
    return cacheIDs

# TODO incorporate class methods into app (IN PROGRESS)
# TODO enable changing call types, w/ hiding/generating components
# TODO add dryrun w/ log in app
# TODO flask caching minimal example works (IN PROGRESS)
# TODO as the cache grows, updatetable() should be getting slices of data
# TODO try using subcorpora calls w/ datatable
# TODO add load
    # Input('upload', 'contents')
    #[State('upload', 'filename')]
    # contents,filename,
    # # upload file
    # if changed_id == "upload.contents":
    #     df = parse_contents(contents, filename)
    #     results = df.round(2).to_dict('records')

@app.callback([
    Output("resultsTable", "data"),
    Output("resultsTable", "columns")], 
    [Input("cacheIDs", "data")])
def updatetable(trigger):
    cacheIDs = cache.get("ledger")
    results = pd.DataFrame()
    if cacheIDs is not None:
        for x in range(len(cacheIDs)):
            hashed = cacheIDs[x]["hash"][0]
            cached = cache.get(hashed)
            results = results.append(cached)
    # results.reset_index(level=0, inplace=True)
    results["#"] = range(len(results))
    columns=[{"name": i, "id": i, "presentation": 'markdown'} for i in results.columns]
    data = results.to_dict('records')
    return data, columns

@app.callback([
    Output("cacheTable", "data"),
    Output("cacheTable", "columns")], 
    [Input("cacheIDs", "data")])
def cacheTable(trigger):
    cacheIDs = cache.get("ledger")
    if cacheIDs is None:
        data = []
        columns = []
    else:
        columns = [{"name": i, "id": i} for i in cacheIDs[0].keys()]
        for x in range(len(cacheIDs)):
            cacheIDs[x]["hash"][0] = cacheIDs[x]["hash"][0][:7]
        data = cacheIDs
    return data, columns
