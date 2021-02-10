import requests
import numpy as np
import time
import re

# TODO test fmaxitems
# TODO get list of all text types and subtypes
# TODO run API calls and visualize results in app

# get login credentials
with open("auth_api.txt") as f:
    LOGIN = dict(x.rstrip().split(":") for x in f)

# get corpus text types
corp_info = np.load("corp_info.npy", allow_pickle="TRUE").item()

# get grammar
with open("grammar.txt") as f:
    lines = [line.rstrip() for line in f]
lines = lines[lines.index("### Pilar's relations start here") :]

# get word sketch names in grammar
wslist = []
for x in range(0, len(lines)):
    if "%" in lines[x]:
        wslist = wslist + lines[x].split("/")
# prep word sketch names for API query
wslist = ['"' + re.sub('.*" ', ".*", w) + '"' for w in wslist]

# define query
b = '[ws(".*-n",' + wslist[1] + ',".*-n")]' + 'within <doc (editor="Goverment") />'
# b = '[ws(".*-n",".*type of.*",".*-n")]'

# make requests
base_url = "https://api.sketchengine.eu/bonito/run.cgi/"
query_type = "freqs?"
cql_query = b
data = {
    "q": "q" + cql_query,
    # "fcrit": [x + " 0<0" for x in corp_info["freqttattrs"]],
    "fcrit": "lemma/e 0~0>0",
    "fmaxitems": "100",
    "corpname": "preloaded/ecolexicon_en",
    "username": LOGIN["username"],
    "api_key": LOGIN["api_key"],
    "async": "0",
    "format": "json",
}
print("... making request")
d = requests.get(base_url + query_type, params=data).json()

# save
np.save("data/PR/precision.npy", d)
# sleep
# time.sleep(4)

# Sketch Engine usage policy:
# <50 requests, no waiting
# <900 requests, 4 seconds per query
# 2000< requests, 44 seconds per query

# to load a file
# freqs = np.load('freqs/freqs145.npy',allow_pickle='TRUE').item()
