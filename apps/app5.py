import dash
import dash_core_components as dcc
import dash_html_components as html
# import dash_daq as daq
import dash_table
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import base64
import io
import pandas as pd
import time
from app import app
import scripts.calls as calls
import scripts.callsa as callsa
import scripts.callsprep as prep
from flask_caching import Cache
import pathlib
import json

cache = Cache(app.server, config={
    'CACHE_TYPE': 'redis',
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR': 'cache-directory',
})

#### VIEW API APP

# TODO #6 run same searches in browser to check data integrity
# TODO #8 add a box for setting other API parameters (corpus info, doc:entry combos)
# TODO #9 add conc links to sketch engine using md in datatable [title](https://www.example.com)
# TODO #13 add metadata cols, make hidden
# TODO make default savesize and other saveable settings
# TODO setup cyclical API calls if all concs are desired when all_concs >10,000 

#### LAYOUT

layout = html.Div(
    [
        dcc.Store(id="cacheIDs", storage_type="session"),
        dcc.Store(id='parameters', storage_type='session'),
        html.H5("Query"),
        html.Div([
            dcc.Dropdown(
                id="querytype",
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
            html.Button('Submit', id='submit', n_clicks=0,
                style={"width": "175px"},),
                ], style={"display": "flex", "flex-wrap": "wrap",},
            ),
        dcc.Textarea(
            id="qmain",
            placeholder="1:[lemma=\"water\"]",
            persistence=True,
            persistence_type="session",
            style={
                "width": "100%",
                "height": "50px",
                }),
        html.H5("Parameters"),
        html.Div([
        dcc.Input(
            id="refs",
            persistence=True,
            persistence_type="session",
            value="doc,s",
            placeholder='refs',
            style={"width": "50%"},
        ),  
        dcc.Dropdown(
            id="corpus",
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
        dcc.Dropdown(
            id="randomize",
            persistence=True,
            persistence_type="session",
            clearable=False,
            placeholder='randomize',
            options=[
                {'label': 'sequential', 'value': '0'},
                {'label': 'random', 'value': '1'}],
            value='0',
            style={"width": "175px"},
        ),
        dcc.Input(
            id="pagesize",
            persistence=True,
            persistence_type="session",
            type="number",
            placeholder="lines",
            value=100,
            min=100,
            max=10000,
            step=100,
            style={"width": "80px"},
        ),],
        style={
            "display": "flex",
            "flex-wrap": "wrap",
            "justify-content": "space-between",
            "align-items":"center",
            },
        ),
        html.H5("Multi-call"),
        dcc.Textarea(
            id="clist",
            persistence=True,
            persistence_type="session",
            placeholder="""# ocean-possessive
"query": ''' 1:[word="ocean's"] '''
# fish-Wikipedia
"query": ''' 1:"fish" ''' , "corpus": "preloaded/enwiki"
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
                html.H5("Results"),
                dash_table.DataTable(
                    id="table",
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
                    style_cell={'textAlign': 'left'},

                )
            ],
            # style={},
        ),
    ], style={'margin': '25px'},
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

# compile api parameters
@app.callback(Output("parameters", "data"),
    [Input("querytype","value"),
    Input("qmain","value"),
    Input("refs","value"),
    Input("corpus","value"),
    Input("qattr","value"),
    Input("viewmode","value"),
    Input("randomize","value"),
    Input("pagesize", "value")])
def parameters(querytype,qmain,refs,corpus,qattr,viewmode,randomize,pagesize):
    parameters = {
    "querytype": querytype,
    "query": qmain,
    "refs": refs,
    "corpname": corpus, 
    "qattr": qattr, 
    "viewmode": viewmode,
    "randomize": randomize, 
    "pagesize": pagesize, 
    "fromp": 1,
    }
    return parameters

# submit API call
@app.callback(Output("cacheIDs","data"),
    [Input("submit", "n_clicks")],
    [State("parameters","data"),
    State("clist","value"),
    State("version","title"),
    State("cacheIDs","data")],
    prevent_initial_call=True)
def submitcall(clicks,parameters,clist,version,cacheIDs):
    print("Starting calls")
    if cacheIDs is None:
        # set cacheIDs
        cacheIDs = []
    if clist:
        # parse list of calls
        calls = calls.ParseCallList(clist, parameters)
    else:
        clist = None
        calls = [parameters]
    # validate calls
    # skip calls with no queries
    calls = [x for x in calls if x["query"]]
    # skip identical calls
    calls = list(set(calls))

    # format parameters by API reqs # this and all other calls should be in one function
    for x in range(len(parameters)):
        # randomize
        if parameters[x]["randomize"] == '1':
            rand = "r" + str(parameters[x]["pagesize"])
        else:
            rand = ""
        # set parameters
        new = {
            "q": [parameters[x]["qattr"] + parameters[x]["query"], rand],
        }
        parameters[x].update(new)
        parameters[x]["querytype"] = "view?"
        del parameters[x]["qattr"]
        del parameters[x]["query"]
        del parameters[x]["randomize"]

    # compare with cached
    for x in range(len(parameters)):
        # make callid
        callID = json.dumps(parameters[x], sort_keys=True)
            # skip API call if already in cache
        if callID in cacheIDs:
            print("... skipping call ", str(x))
        else:
            # make calls and cache results, w/ API throttling
            print("... making call", str(x))
            # do call
            results = calls.BasicCall(parameters[x])
            calls.wait(len(parameters))
            # process raw data
            results = prep.ViewPrep([results], clist)
            # add to cache
            cache.set(callID, results)
            cacheIDs.append(callID)
    return cacheIDs

# TODO flask caching minimal example works
# but basiccall, multicall, and view etc. functions need to be optimized for caching 
# (while still allowing terminal use)
# as the cache grows, updatetable() should be getting slices of data
# more components need to be added to manage cache and its usage in the app
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
    Output("table", "data"),
    Output("table", "columns")], 
    [Input("cacheIDs", "data")],
    prevent_initial_call=True)
def updatetable(cacheIDs):
    results = []
    for x in range(len(cacheIDs)):
        results.extend(cache.get(cacheIDs[x]))
    if results:
        columns=[{"name": i, "id": i, "type": 'text', "presentation": 'markdown'} for i in results[0].keys()]
        return results, columns
    else:
        raise PreventUpdate