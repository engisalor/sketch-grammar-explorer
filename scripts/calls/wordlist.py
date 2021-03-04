import requests
import time
import json
import pandas as pd
from datetime import datetime
import re
from pathlib import Path

### 
# template for wordlist calls (total frqs for a text type) 
###

def wordlist(attr, corpus = "preloaded/ecolexicon_en", format = "json", maxitems = 1000):
    query_type = "wordlist?"
    # set parameters
    settings = {
        "corpname": corpus,
        "wlattr": attr,
        "wlmaxitems":maxitems,
        "wltype": "simple",
        "format": "json",
        "wlsort": "frq",
        "subcnorm":"frq",
        "usesubcorp":"",
        "wlpat":".*",
        "wlminfreq":1,
        "wlicase":1,
        "wlmaxfreq":0,
        "wlfile":"",
        "wlblacklist":"",
        "wlnums":"",
        "include_nonwords":1,
        "wlstruct_attr1":"",
        "wlstruct_attr2":"",
        "wlstruct_attr3":"",
        "random":0,
        "relfreq":1,
        "reldocf":1,
        "wlpage":1,        
        }
    return settings, query_type
