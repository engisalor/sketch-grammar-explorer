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
        html.H6(children="View API"),
        dcc.Textarea(
            id="textarea",
            placeholder="CQL query",
            style={
                "display": "inline-flex",
                "width": "50%",
                }),
        html.P(),
        html.Button('Submit', id='submit', n_clicks=0),
        dcc.RadioItems(
            id='qattr',
            options=[
                {'label': 'lemma', 'value': 'alemma,'},
                {'label': 'word', 'value': 'aword,'},
                {'label': 'tag', 'value': 'atag,'},
                {'label': 'lempos', 'value': 'alempos,'},
                {'label': 'lempos_lc', 'value': 'alempos_lc,'},
                {'label': 'lemma_lc', 'value': 'alemma_lc,'},
                {'label': 'word_lc', 'value': 'aword_lc,'},
                {'label': 'multi_q', 'value': ''} # FIXME troubleshoot how this works
            ],
            value='alemma,',
            labelStyle={'display': 'inline-block'}
        ),
        dcc.RadioItems(
            id="viewmode",
            options=[
                {'label': 'sentence', 'value': 'sen'},
                {'label': 'KWIC', 'value': 'kwic'}],
            value='sen',
            labelStyle={'display': 'inline-block'}
        ),  
        dcc.RadioItems(
            id="randomize",
            options=[
                {'label': 'sequential', 'value': '0'},
                {'label': 'random', 'value': '1'}],
            value='0',
            labelStyle={'display': 'inline-block'}
        ),
        dcc.Input(
            id="pagesize",
            type="number",
            placeholder="lines (100<10,000)",
            min=100,
            max=10000,
            step=100
        ),
        html.Div([
        dcc.Loading(
        id="loading",
        children=[html.Div([html.Div(id="loading_output")])],
        type="circle")],
            style={
                "display": "inline-flex",
                "width": "25%",
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

# submit api query
@app.callback([Output("loading_output", "children"),
    Output("table", "data"),
    Output("table", "columns")], 
    [Input("submit", "n_clicks"),
    Input('upload', 'contents')],
    [State('upload', 'filename'),
    State("pagesize", "value"),
    State("randomize","value"),
    State("textarea","value"),
    State("version","title"),
    State("qattr","value"),
    State("viewmode","value")])
def updatetable(clicks,contents,filename,pagesize,randomize,textarea,version,qattr,viewmode):
    # get last triggered callback
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]

    # upload file
    if changed_id == "upload.contents":
        df = parse_contents(contents, filename)
        return "", df.round(2).to_dict('records'), [{"name": i, "id": i, "type": 'text', "presentation": 'markdown'} for i in df.columns]

    # submit api call
    if changed_id == "submit.n_clicks":
        # default pagesize
        if pagesize == "" or pagesize is None:
            pagesize = 100
        # make query parameters
        queries = ("view", [{
            "query": textarea, 
            "corpus": "preloaded/ecolexicon_en", 
            "qattr": qattr, 
            "randomize": randomize, 
            "pagesize": pagesize, 
            "fromp": 1, # TODO add checkbox to cycle through all fromp after first result if > 10,000 results
            "viewmode": viewmode
            }])
        # do call
        results = callsa.MultiCall(queries)
        # do preprocessing
        results = prep.ViewPrep(results)
        # add markdown coding in table
        columns=[{"name": i, "id": i, "type": 'text', "presentation": 'markdown'} for i in results[0].keys()]
        return '', results, columns
    
    # prevent undesired updates
    else:
        raise PreventUpdate