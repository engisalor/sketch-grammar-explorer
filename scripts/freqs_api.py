import requests
import numpy as np
import time
import re

### 
# this script saves api calls for each rule in a sketch grammar 
# rules are identified by line number (starting at 0)
# grammar.txt is based on Sketch Engine's sketch grammar file
# modifications may be needed to run a new file for first time 
###

# get login credentials
with open(".auth_api.txt") as f:
    LOGIN = dict(x.rstrip().split(":") for x in f)

# get corpus text types
corp_info = np.load("corp_info.npy", allow_pickle="TRUE").item()

# get grammar
with open("grammar.txt") as f:
    lines = [line.rstrip() for line in f]
lines = lines[lines.index("### Pilar's relations start here") :]

# get indexes of CQL rules
cqllines = [i for i, x in enumerate(lines) if "[" in x]

# make dict of relations & CQL expressions
dt = {}
for i in range(0, len(cqllines)):
    rslice = reversed(lines[: cqllines[i]])
    relation = next((x for x in rslice if "#" in x), ["NA"])
    dt[cqllines[i]] = [relation, lines[cqllines[i]]]

# modify CQL rules
for x in dt:
    # change default attribute syntax ("N.*" to [tag="N.*"])
    dt[x][1] = re.sub('(?<!=)("[\|\.\*A-Z]+")', "[tag=\g<0>]", dt[x][1]) 
    # limit to within sentence
    dt[x][1] = dt[x][1] + ' within <s/>'

# make requests
for x in dt[7]: # or "for x in [INDEX]:" for a single query
    base_url = "https://api.sketchengine.eu/bonito/run.cgi/"
    query_type = "freqs?"
    cql_query = dt[x][1]
    data = {
        "q": "q" + cql_query,
        "fcrit": [x + " 0<0" for x in corp_info["freqttattrs"]],
        "corpname": "preloaded/ecolexicon_en",
        "username": LOGIN["username"],
        "api_key": LOGIN["api_key"],
        "async": "0",
        "format": "json"}
    print("... making request " + str(x))
    d = requests.get(base_url + query_type, params=data).json()
    # save
    np.save("data/freqs/freqs" + str(x) + ".npy", d)
    # sleep
    time.sleep(4)

# Sketch Engine usage policy:
# <50 requests, no waiting
# <900 requests, 4 seconds per query
# 2000< requests, 44 seconds per query

# to load a file
# freqs = np.load('freqs/freqs145.npy',allow_pickle='TRUE').item()
