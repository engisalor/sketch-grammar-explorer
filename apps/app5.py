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
# import time
from app import app
import scripts.callsprep as prep
from flask_caching import Cache
import pathlib
import json
import scripts.classes as classes
import ast

cache = Cache(app.server, config={
    'CACHE_TYPE': 'redis',
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR': 'cache-directory',
})

def getcacheIDs(filepath=".cacheIDs.txt"):
    filepath = pathlib.Path(filepath)
    with open(filepath) as f:
        return [ast.literal_eval(x) for x in f if x]

def setcacheIDs(cachIDs, filepath=".cacheIDs.txt"):
    filepath = pathlib.Path(filepath)
    with open(filepath, 'w') as f:
        for item in cachIDs:
            f.writelines(str(item)+"\n")

#### VIEW API APP

# TODO #6 run same searches in browser to check data integrity
# TODO #8 add a box for setting other API params (corpus info, doc:entry combos)
# TODO #9 add conc links to sketch engine using md in datatable [title](https://www.example.com)
# TODO #13 add metadata cols, make hidden
# TODO make default savesize and other saveable settings
# TODO setup cyclical API calls if all concs are desired when all_concs >10,000 

#### LAYOUT

layout = html.Div(
    [
        dcc.Store(id="cacheIDs", storage_type="session", data=getcacheIDs()),
        dcc.Store(id='params', storage_type='session'),
        dcc.Store(id='settings', storage_type='session'),
        html.H5("Query"),
        html.Div([
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
        html.H5("params"),
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
"q": ''' 1:[word="ocean's"] '''
# fish-Wikipedia
"q": ''' 1:"fish" ''' , "corpus": "preloaded/enwiki"
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
                html.H5("Cached"),
                dcc.Textarea(
                    id="cached",
                    placeholder="cached queries",
                    persistence=True,
                    persistence_type="session",
                    readOnly=True,
                    style={
                        "width": "100%",
                        "height": "50px",
                        }),
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

# get params
@app.callback(Output("params", "data"),
    [Input("qmain","value"),
    Input("refs","value"),
    Input("corpus","value"),
    Input("viewmode","value"),
    Input("pagesize", "value")])
def params(qmain,refs,corpus,viewmode,pagesize):
    params = {
        "q": qmain,
        "refs": refs,
        "corpname": corpus, 
        "viewmode": viewmode,
        "pagesize": pagesize, 
        "fromp": 1}
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
    [Input("submit", "n_clicks")],
    [State("params","data"),
    State("settings","data"),
    State("clist","value"),
    State("cacheIDs","data")],
    prevent_initial_call=False)
def submitcall(clicks,params,settings,clist,cacheIDs):
    ctx = dash.callback_context
    if not ctx.triggered:
        button_id = None
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if button_id == "submit":
        # make instance
        c = getattr(classes,settings["calltype"])(params,settings,clist)
        # do calls
        cacheIDs = c.makecalls(cache=cache,cacheIDs=cacheIDs) # TODO add labels, etc., to cacheIDs
        setcacheIDs(cacheIDs)
    return cacheIDs

# TODO allow copy/paste from cache textarea to multi-call textarea
# this requires improving handling of quotes and escaping ', "", '''
# TODO compare how big the cache is when raw json data vs after Prep script
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
    Output("table", "data"),
    Output("table", "columns")], 
    [Input("cacheIDs", "data")])
def updatetable(cacheIDs):
    # TODO all this needs work (get slices instead of whole dataset)
    if cacheIDs is None:
        cacheIDs = getcacheIDs()
    try:
        for x in range(len(cacheIDs)):
            results = cache.get(cacheIDs[x]["hash"])
        if results:
            columns=[{"name": i, "id": i, "type": 'text', "presentation": 'markdown'} for i in results[0].keys()]
            return results, columns
    except:
        raise PreventUpdate

# show cachedIDs in textarea
@app.callback(
    Output("cached", "value"),
    Input("cacheIDs", "data"))
def updatetable(cacheIDs):
    if cacheIDs:
        return "\n".join([str(x["call"]) for x in cacheIDs])
    else:
        raise PreventUpdate