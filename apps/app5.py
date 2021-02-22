import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_daq as daq
import dash_table
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import base64
import io
import pandas as pd
import time
from app import app
from scripts.view_api import view_api
from scripts.view_prep import view_prep

#### VIEW API APP

# TODO #6 run same searches in browser to check data integrity
# TODO #8 add a box for setting other API parameters (corpus info, doc:entry combos)
# TODO #9 add conc links to sketch engine using md in datatable [title](https://www.example.com)
# TODO #13 add metadata cols, make hidden

#### LAYOUT

layout = html.Div(
    [
        html.H6(children="Precision Analysis"),
        dcc.Textarea(
            id="textarea",
            placeholder="CQL query",
            style={
                "display": "inline-flex",
                "width": "50%",
                }),
        html.P(),
        html.Div([
            daq.BooleanSwitch(
            id="switch",
            on=False,
            label="random",
            labelPosition="bottom"),
            dcc.Input(
            id="sample",
            type="number",
            placeholder="sample size",
            step=100,
            value=500),
            html.Button('Submit', id='submit', n_clicks=0),
            ],
            style={
                "display": "inline-flex",
                "width": "25%",
                "justify-content": "space-around",
            },
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
            'width': '25%', 'height': '30px', 'lineHeight': '30px',
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
    State("sample", "value"),
    State("switch","on"),
    State("textarea","value"),
    State("version","title")])
def updatetable(clicks,contents,filename,sample,switch,textarea,version):
    # get last triggered callback
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]

    # upload file
    if changed_id == "upload.contents":
        df = parse_contents(contents, filename)
        return "", df.round(2).to_dict('records'), [{"name": i, "id": i, "type": 'text', "presentation": 'markdown'} for i in df.columns]

    # submit api call
    if changed_id == "submit.n_clicks":
        # do call
        d = view_api(textarea, switch, sample)
        # do preprocessing
        df = view_prep(d,version)
        # add markdown coding in table
        columns=[{"name": i, "id": i, "type": 'text', "presentation": 'markdown'} for i in df.columns]
        return '', df.round(2).to_dict("records"), columns
    
    # prevent undesired updates
    else:
        raise PreventUpdate






