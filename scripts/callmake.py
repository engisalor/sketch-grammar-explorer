import requests
import time
import json
import pandas as pd
from datetime import datetime
import re
from pathlib import Path
from scripts.calls.corpinfo import corpinfo
from scripts.calls.freqs import freqs
from scripts.calls.view import view
from scripts.calls.basiccall import basiccall

###
# run API calls of different types and return results
###

### VIEW CALL
# settings, query_type = view(
#     query = '[lemma="test"]', 
#     corpus = "preloaded/ecolexicon_en", 
#     qattr = 'q', 
#     randomize = False, 
#     pagesize = 20, 
#     fromp = 1, 
#     viewmode = "sen")


### FREQS CALL
# get corpus info
info = corpinfo(False)
# get corpus structures
dt = {}
for y in range(len(info["structs"])):
    for x in range(len(info["structs"][y][2])):
        dt[info["structs"][y][2][x][0]] = info["structs"][y][2][x][2]
# set text types
if info["request"]["corpname"] == "user/PilarLeon/hejuly2019_backup":
    for x in ["doc.id","doc.filename","doc.wordcount"]: 
        dt.pop(x)
if info["request"]["corpname"] == "preloaded/ecolexicon_en":
    for x in ["doc.author","doc.keywords","doc.title","doc.wordcount"]: 
        dt.pop(x)
ttypes = list(dt.keys())

# set shape of results and ttypes
fcrit = [x + " 0" for x in ttypes]

# define call
settings, query_type = freqs(
    query = '[lemma="test"]',
    fcrit = fcrit,
    corpus = "preloaded/ecolexicon_en", 
    )

# RUN CALL
f = basiccall(
    query_type,
    settings,
    # corpus = "preloaded/ecolexicon_en", 
    )