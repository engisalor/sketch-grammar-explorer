import requests
import numpy as np
import pandas as pd
import time
import re

####
# this script retrives word sketch frequencies for:
# * a specific relation (is a type of..., caused by, etc.) as defined in a sketch grammar
# * using a list of corpus text types (Editor, Domain, etc.)
# * and all of their entries (Academic, Government, etc.)
# it's not designed for text types with thousands of entries (author, key words, etc.)
#
# note: the Domain ttype must be made plural for the API request to work
####

# TODO test fmaxitems
# TODO run API calls and visualize results in app

# get login credentials
with open(".auth_api.txt") as f:
    LOGIN = dict(x.rstrip().split(":") for x in f)

# get corpus text types
df = pd.read_csv("data/ttypes.csv")
# change text types to plural
df.loc[(df["ttype"] == "Domain"), "ttype"] = "Domains"
# corpinfo = np.load("corpinfo.npy", allow_pickle="TRUE").item() # secondary method

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


# make requests
for x, y in df.filter(["ttype", "item"], axis=1).to_numpy():  # for all ttypes
    # for x,y in np.array([['Domains', 'Biology']]): # for a single pair
    # define query
    wstype = wslist[1]  # pick one wstype here
    ttypestr = "within <doc (" + x.lower() + '="' + y + '") />'
    b = '[ws(".*-n",' + wstype + ',".*-n")]' + ttypestr
    # b = '[ws(".*-n",".*type of.*",".*-n")]' # a generic search

    # make url
    base_url = "https://api.sketchengine.eu/bonito/run.cgi/"
    query_type = "freqs?"
    cql_query = b
    data = {
        "q": "q" + cql_query,
        "fcrit": "lemma/e 0~0>0",
        "fmaxitems": "100",
        "corpname": "preloaded/ecolexicon_en",
        "username": LOGIN["username"],
        "api_key": LOGIN["api_key"],
        "async": "0",
        "format": "json",
    }
    print("... making request " + wstype + " " + x + "_" + y)
    d = requests.get(base_url + query_type, params=data).json()

    # save
    filename = (
        "".join(filter(str.isalpha, wstype))
        + "_"
        + "".join(filter(str.isalpha, x))
        + "_"
        + "".join(filter(str.isalpha, y))
    )
    np.save("data/ws/ws_freqs_" + filename, d)
    # sleep
    time.sleep(4)

# Sketch Engine usage policy:
# <50 requests, no waiting
# <900 requests, 4 seconds per query
# 2000< requests, 44 seconds per query

# to load a file
# freqs = np.load('freqs/freqs145.npy',allow_pickle='TRUE').item()
