import requests
import time
import json
import pandas as pd
from datetime import datetime
import re
from pathlib import Path

###
# basic format for API calls using templates
###

def basiccall(
    query_type,
    settings,
    corpus = "preloaded/ecolexicon_en", 
    ):

    # set file paths
    data_folder = Path("")
    fauth = data_folder / ".auth_api.txt"

    # get login credentials
    with open(fauth) as f:
        LOGIN = dict(x.rstrip().split(":") for x in f)

    # get time
    now = datetime.now().strftime("%Y-%m-%d %H.%M.%S")
    
    # combine parameters
    data = {
        "username": LOGIN["username"],
        "api_key": LOGIN["api_key"],
        "asyn": "0",
        "format": "json",
    }
    alldata = {**data, **settings}

    # run request
    print("...calling ", query_type, "\n...",settings)
    d = requests.get("https://api.sketchengine.eu/bonito/run.cgi/" + query_type, params=alldata).json()

    # errors
    if "error" in d:
        print("API error: ", d["error"])

    # return
    else:
        print("DONE\n")
        return d