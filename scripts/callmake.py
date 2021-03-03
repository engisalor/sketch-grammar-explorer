import requests
import time
import json
import pandas as pd
from datetime import datetime
import re
from pathlib import Path
from scripts.calls.corpinfo import corpinfo
from scripts.calls.attrvals import attrvals
from scripts.calls.wordlist import wordlist
from scripts.calls.freqs import freqs
from scripts.calls.view import view
from scripts.calls.basiccall import basiccall

###
# run API calls of different types and return results
###

### CORP INFO CALL
settings, query_type = corpinfo()

### ATTR VALS CALL ***BROKEN***
settings, query_type = attrvals(
    avattr = "doc.domains", 
    # avpat = None, 
    # maxitems = 10,
    # corpus = "preloaded/ecolexicon_en"
    )

### VIEW CALL
settings, query_type = view(
    query = '[lemma="test"]', 
    corpus = "preloaded/ecolexicon_en", 
    qattr = 'q', 
    randomize = False, 
    pagesize = 20, 
    fromp = 1, 
    viewmode = "sen"
    )

### FREQS CALL
settings, query_type = freqs(
    query = '[lemma="test"]',
    fcrit = fcrit,
    corpus = "preloaded/ecolexicon_en")

### FREQS HITS PER DOC / SENTENCE CALL
settings, query_type = freqs(
    query = '[lemma="test"]',
    fcrit = 'doc 0 s 0',
    corpus = "preloaded/ecolexicon_en")

### WORD SKETCH FREQS

# 1 get text types

# 2 get word sketch names in grammar
wslist = []
for x in range(0, len(lines)):
    if "%" in lines[x]:
        wslist = wslist + lines[x].split("/")

# prep word sketch names for API query
wslist = ['"' + re.sub('.*" ', ".*", w) + '"' for w in wslist]


# make requests
for x,y in df.filter(["ttype", "item"], axis=1).to_numpy(): # for all ttypes
# for x,y in np.array([['Domains', 'Biology']]): # for a single pair
    # define query
    wstype = wslist[1] # pick one wstype here
    ttypestr = 'within <doc (' + x.lower() + '="' + y + '") />'
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

    }

# WORDLIST CALL ***BROKEN***
settings, query_type = wordlist("")
query_type

# RUN CALL
f = basiccall(
    query_type,
    settings,
    # corpus = "preloaded/ecolexicon_en", 
    )
f

# for splitting csv formatted results: f.split("\n")