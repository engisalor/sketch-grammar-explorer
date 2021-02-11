import requests
import numpy as np
import pandas as pd
import time
import re

# get login credentials
with open("auth_api.txt") as f:
    LOGIN = dict(x.rstrip().split(":") for x in f)

# get corpus text types
corp_info = np.load("corp_info.npy", allow_pickle="TRUE").item()

# make request
base_url = "https://api.sketchengine.eu/bonito/run.cgi/"
query_type = "freqs?"
cql_query = "<doc/>"
data = {
    "q": "q" + cql_query,
    "fcrit": [x + " 0" for x in ['doc.domains', 'doc.genre', 'doc.editor','doc.user']],
    "corpname": "preloaded/ecolexicon_en",
    "username": LOGIN["username"],
    "api_key": LOGIN["api_key"],
    "async": "0",
    "format": "json"}
print("... making request ")
d = requests.get(base_url + query_type, params=data).json()
# save
np.save("data/PR/ttypes.npy", d)

#### make DF of text types

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

temp.to_csv("data/ttypes/ttypes.csv",index=False)
