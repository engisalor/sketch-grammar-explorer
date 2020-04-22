import requests
import numpy as np
import time
import re

# get login credentials
with open("auth_api.txt") as f:
    LOGIN = dict(x.rstrip().split(":") for x in f)

# get corpus text types
corp_info = np.load("corp_info.npy", allow_pickle="TRUE").item()

# get grammar
with open("grammar.txt") as f:
    lines = [line.rstrip() for line in f]
lines = lines[lines.index("### Pilar's relations start here") :]

# get indexes of CQL lines
cqllines = [i for i, x in enumerate(lines) if "[" in x]

# make dict of gramrels & CQL
dt = {}
for i in range(0, len(cqllines)):
    rslice = reversed(lines[: cqllines[i]])
    gramrel = next((x for x in rslice if "#" in x), ["NA"])
    dt[cqllines[i]] = [gramrel, lines[cqllines[i]]]

# modify default attribute syntax ("N.*" becomes [tag="N.*"])
for x in dt:
    dt[x][1] = re.sub('(?<!=)("[\|\.\*A-Z]+")', "[tag=\g<0>]", dt[x][1])

    # do requests
    # for x in dt: # all queries
    # for x in [145]: # single query by ref#
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
        "format": "json",
    }

    d = requests.get(base_url + query_type, params=data).json()
    d

    # save
    np.save("freqs/freqs" + str(x) + ".npy", d)

    # sleep
    time.sleep(4)
    # Sketch Engine usage policy:
    # <50 requests, no waiting
    # <900 requests, 4 seconds per query
    # 2000< requests, 44 seconds per query

# load a file
# freqs = np.load('freqs/freqs145.npy',allow_pickle='TRUE').item()
