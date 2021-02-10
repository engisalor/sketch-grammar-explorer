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
