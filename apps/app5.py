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
        dcc.Store(id='parameters'),
        html.H6(children="SkE API interface"),
        html.P("Query type"),
        html.Div([
        dcc.Dropdown(
            id="querytype",
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

        html.P("CQL rule"),
        dcc.Textarea(
            id="qmain",
            placeholder="1:[lemma=\"water\"]",
            style={
                "width": "100%",
                "height": "50px",
                }),
        html.P("Parameters"),
        html.Div([
        dcc.Input(
            id="refs",
            debounce=True,
            value="doc,s",
            placeholder='refs',
            style={"width": "50%"},
        ),  
        dcc.Dropdown(
            id="corpus",
            placeholder='corpus',
            options=[
                {'label': 'ecolexicon_en', 'value': 'preloaded/ecolexicon_en'},
                ],
            value="preloaded/ecolexicon_en",
            style={"width": "175px"},
        ),  
        dcc.Dropdown(
            id='qattr',
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
        },
        ),
        html.P("Multiple calls"),
        dcc.Textarea(
            id="clist",
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
        html.P(),
        html.Div([
        dcc.Loading(
        id="loading",
        children=[html.Div([html.Div(id="loading_output")])],
        type="circle")],
            style={
                "display": "inline-flex",
                "width": "100%",
                "justify-content": "space-around",
            },
),
        html.P(),
        dcc.Upload(
        id='upload',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select Files')
        ]),
        style={
            'width': '250px', 'height': '30px', 'lineHeight': '30px',
            'borderWidth': '1px', 'borderStyle': 'dashed',
            'borderRadius': '5px', 'textAlign': 'center', 'margin': '10px'
        },
    ),
        html.P(),
        html.Div(
            [
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
                    page_size=100,
                    style_table={
                        "overflowX": "scroll",
                        "maxHeight": "800px",
                        "overflowY": "scroll",
                    },
                    style_data={"whiteSpace": "normal", "height": "auto"},
                    style_cell={'textAlign': 'left'},

                )
            ],
            style={"width": "100%"},
        ),
    ]
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
    Input("qmain","n_blur"),
    Input("refs","value"),
    Input("corpus","value"),
    Input("qattr","value"),
    Input("viewmode","value"),
    Input("randomize","value"),
    Input("pagesize", "value"),],
    [State("qmain","value")])
def parameters(querytype,qmainblur,refs,corpus,qattr,viewmode,randomize,pagesize,qmain):
    parameters = (querytype, [{
    "query": qmain,
    "refs": refs,
    "corpus": corpus, 
    "qattr": qattr, 
    "viewmode": viewmode,
    "randomize": randomize, 
    "pagesize": pagesize, 
    "fromp": 1,
    }])
    return parameters

# submit api query
@app.callback([Output("loading_output", "children"),
    Output("table", "data"),
    Output("table", "columns")], 
    [Input("submit", "n_clicks"),
    Input('upload', 'contents')],
    [State('upload', 'filename'),
    State("parameters","data"),
    State("clist","value"),
    State("version","title"),
    ])
def updatetable(clicks,contents,filename,parameters,clist,version):
    # get last triggered callback
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]

    # upload file
    if changed_id == "upload.contents":
        df = parse_contents(contents, filename)
        return "", df.round(2).to_dict('records'), [{"name": i, "id": i, "type": 'text', "presentation": 'markdown'} for i in df.columns]

    # FIXME test w/ various combos and debug (e.g., mixing qmain with clist, multiple fromp)
    # submit api call
    if changed_id == "submit.n_clicks":
        # if list of calls
        if clist:
            # fill parameters for each item in clist
            clist = calls.ParseCallList(clist)
            parameters[1] = [parameters[1][0] for x in range(len(clist))]
            # update unique parameters for each item
            for x in range(len(clist)):
                parameters[1][x] = {**parameters[1][x], **clist[x][1]}
        # do call 
        results = callsa.MultiCall(parameters)
        # prep for datatable
        results = prep.ViewPrep(results, clist)
        # define columns and add markdown encoding
        columns=[{"name": i, "id": i, "type": 'text', "presentation": 'markdown'} for i in results[0].keys()]
        return '', results, columns
    
    # prevent undesired updates
    else:
        raise PreventUpdate