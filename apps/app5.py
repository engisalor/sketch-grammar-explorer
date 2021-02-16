import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_daq as daq
import dash_table
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import base64
import io
import numpy as np
import pandas as pd
import re
import requests
import time
from app import app

#### GET DATA
# d = np.load('data/view/TEST.npy',allow_pickle='TRUE').item()

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
                    # data=df.round(2).to_dict("records"),
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
    State("textarea","value")])
def input_triggers_spinner(clicks,contents,filename,sample,switch,textarea):
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    # upload file
    if changed_id == "upload.contents":
        df = parse_contents(contents, filename)
        return "", df.round(2).to_dict('records'), [{"name": i, "id": i, "type": 'text', "presentation": 'markdown'} for i in df.columns]

    # submit api call
    if changed_id == "submit.n_clicks":
        # get login credentials
        with open(".auth_api.txt") as f:
            LOGIN = dict(x.rstrip().split(":") for x in f)

        # make url
        base_url = "https://api.sketchengine.eu/bonito/run.cgi/"
        query_type = "view?"
        cql_query = "q" + textarea # e.g. '1:[lemma="climate"] []{1,10} 2:[lemma="change"]'
        # random sample
        if switch == True:
            rand = "r" + str(sample)
        else:
            rand = ""

        data = {
            "q": [cql_query, rand], 
            # TODO try list of queries w/ ‘q=item1;q=item2…’
            "corpname": "preloaded/ecolexicon_en",
            "username": LOGIN["username"],
            "api_key": LOGIN["api_key"],
            "viewmode": "sen", # sen or kwic
            "asyn": "0",
            "pagesize": sample,
            # "attrs": "",
            # "structs": "",
            "refs": "doc,s",
            "format": "json",
        }
        print("... making request ")

        d = requests.get(base_url + query_type, params=data).json()

        # error handling  
        if "error" in d:
            print(d["error"])

        #### PREP DATA

        # create df
        temp = pd.DataFrame()
        for x in d["Lines"]:
            temp = temp.append(pd.DataFrame.from_dict(x, orient="index").T)

        # create concordance w bold kwic elements 
        for x in range(0, len(d["Lines"])):
            ls = []
            for y in range(0,len(d["Lines"][x]["Kwic"])):
                # add ** around labelled kwic items
                if d["Lines"][x]["Kwic"][y]["class"] == 'col0 coll coll':
                    d["Lines"][x]["Kwic"][y]["str"] = "**" + d["Lines"][x]["Kwic"][y]["str"] + "**"
                # combine kwic elements
                ls.append(d["Lines"][x]["Kwic"][y]["str"])
            d["Lines"][x]["fullkwic"] = "".join(ls)
            #combine full conc
            left = "".join([d["Lines"][x]["Left"][y]["str"] for y in range(0,len(d["Lines"][x]["Left"]))])
            right = "".join([d["Lines"][x]["Right"][y]["str"] for y in range(0,len(d["Lines"][x]["Right"]))])
            d["Lines"][x]["conc"] = left + d["Lines"][x]["fullkwic"] + right

        # create columns
        temp["doc"] = [int(re.sub("\D", "",temp.iloc[x]["Refs"][0])) for x in range(0, len(temp["Refs"]))]
        temp["s"] = [int(re.sub("\D", "",temp.iloc[x]["Refs"][1])) for x in range(0, len(temp["Refs"]))]
        temp["conc"] = [d["Lines"][x]["conc"] for x in range(0, len(d["Lines"]))]
        temp["concsize"] = d["concsize"]
        temp["relsize"] = d["relsize"]
        temp["#"] = range(0, len(temp))
        temp["precise"] = ""

        # TODO use md links to go to sketch engine [title](https://www.example.com)

        # filter columns
        df = temp.filter(["#", "precise", "doc", "s", "conc","concsize","relsize"], axis=1).sort_values(by="s", ascending=True)

        # add markdown coding in table
        columns=[{"name": i, "id": i, "type": 'text', "presentation": 'markdown'} for i in df.columns]

        return '', df.round(2).to_dict("records"), columns

    else:
        raise PreventUpdate






