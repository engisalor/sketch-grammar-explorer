import requests
import numpy as np
import pandas as pd
import time
import re

#### 
####

# get login credentials
with open(".auth_api.txt") as f:
    LOGIN = dict(x.rstrip().split(":") for x in f)

# make url
base_url = "https://api.sketchengine.eu/bonito/run.cgi/"
query_type = "view?"
cql_query = "q" + '1:[lemma="climate"] []{1,10} 2:[lemma="change"]'
rand = "r10"
data = {
    "q": [cql_query, rand], 
    # "r": "r200", NOT RIGHT
    # TODO try list of queries w/ ‘q=item1;q=item2…’
    # TODO try getting random sample: r250 instead of q
    "corpname": "preloaded/ecolexicon_en",
    "username": LOGIN["username"],
    "api_key": LOGIN["api_key"],
    "viewmode": "sen", # sen or kwic
    "asyn": "0",
    "pagesize": "20",
    # "attrs": "doc.id,s",
    # "structs": "doc.id,s",
    "refs": "doc,s",
    "format": "json",
}
print("... making request ")
d = requests.get(base_url + query_type, params=data).json()
# save
# np.save("data/view/TEST.npy", d)

d
