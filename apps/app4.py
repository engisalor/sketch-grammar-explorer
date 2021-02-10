import dash
import dash_html_components as html
import dash_table
import pandas as pd
import numpy as np
import re
from app import app

#### GET DATA

# load
ttypes = np.load('data/PR/ttypes.npy',allow_pickle='TRUE').item()

# create df and fill with blocks
freqs1 = [ttypes["Blocks"][x]["Items"] for x in range(0, len(ttypes["Blocks"]))]
temp = pd.DataFrame()
for x in range(0, len(freqs1)):
    temp = temp.append(pd.DataFrame.from_dict(freqs1[x]))

# add second index
temp.reset_index(inplace=True)

# add text type column
ls = []
for x in range(0, len(ttypes['Blocks'])):
    ls = ls + [(ttypes['Blocks'][x]['Head'][0]['n'])] * len(ttypes["Blocks"][x]["Items"])
temp["ttype"] = ls

# add item column
temp["item"] = range(0,len(temp))
for x in range(0,len(temp)):
    temp["item"][x] =  re.search(r" '.*'}",str(temp["Word"][x])).group(0)
    temp["item"][x] = temp["item"][x][2:-2]

# add index1
temp["all"] = range(0, len(temp))

# get relevant columns to graph
temp = temp.filter(["all", "index", "ttype", "item", "frq", "norm", "rel", "fpm"], axis=1)

#### LAYOUT

layout = html.Div(
    [
        html.H6(children="Text type data"),
        html.Div(
            [
                dash_table.DataTable(
                    id="table2",
                    data=temp.round(2).to_dict("records"),
                    columns=[
                        {"id": c, "name": c}
                        for c in temp.columns
                    ],
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
    ]
)
