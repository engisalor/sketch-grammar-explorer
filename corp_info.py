import requests
import numpy as np

# get authentication pairs
with open("auth_api.txt") as f:
    LOGIN = dict(x.rstrip().split(":") for x in f)

# set up request
base_url = "https://api.sketchengine.eu/bonito/run.cgi/"
query_type = "corp_info?"
data = {
    "subcorpora": "1",
    "struct_attr_stats": "1",
    "corpname": "preloaded/ecolexicon_en",
    "username": LOGIN["username"],
    "api_key": LOGIN["api_key"],
    "async": "0",
    "format": "json",
}

# get data
d = requests.get(base_url + query_type, params=data).json()

# save
np.save("corp_info.npy", d)

# to load file
# corp_info = np.load('corp_info.npy',allow_pickle='TRUE').item()