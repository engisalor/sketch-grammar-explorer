import scripts.calls as calls
import scripts.callsa as callsa
import scripts.callsb as callsb
import scripts.callsprep as prep
import json
###
# API call examples and related functions
###

# get word sketches from a grammar
wstypes = callsa.WStypes()

# get corpus info
queries = ("corpinfo", [{
    "corpus": "preloaded/ecolexicon_en"
    }])
info = callsa.MultiCall(queries)

# get structures from corpus
queries = ("corpinfo", [{
    "corpus": "preloaded/ecolexicon_en"
    }])
info = callsa.MultiCall(queries)
structs = callsa.Structs(info)

# get ttypes from corpus
queries = ("corpinfo", [{
    "corpus": "preloaded/ecolexicon_en"
    }])
records = callsb.TTypes(queries)

# WS FREQS # TODO
# need wstypes and ttypes
# make requests
for x,y in df.filter(["ttype", "item"], axis=1).to_numpy(): # for all ttypes
# for x,y in np.array([['Domains', 'Biology']]): # for a single pair
    # define query
    wstype = wslist[1] # pick one wstype here
    ttypestr = 'within <doc (' + x.lower() + '="' + y + '") />'
    b = '[ws(".*-n",' + wstype + ',".*-n")]' + ttypestr
    # b = '[ws(".*-n",".*type of.*",".*-n")]' # a generic search
    # make url
    cql_query = b
    data = {
        "q": "q" + cql_query,
        "fcrit": "lemma/e 0~0>0",
        "fmaxitems": "100",
    }


# attr vals call
queries = ("attrvals", [{    
    "avattr": "doc.domains", 
    "avpat": None, 
    "maxitems": 10,
    "corpus": "preloaded/ecolexicon_en"
    }])

# view call
queries = ("view", [{
    "query": 'lemma,"water"', 
    "corpus": "preloaded/ecolexicon_en", 
    "qattr": 'a', 
    "randomize": '1', 
    "pagesize": 1000, 
    "fromp": 1, 
    "viewmode": "sen"
    },
    {
    "query": 'lemma,"sand"', 
    "corpus": "preloaded/ecolexicon_en", 
    "qattr": 'a', 
    "randomize": '1', 
    "pagesize": 1000, 
    "fromp": 1, 
    "viewmode": "sen"
    }])
results = callsa.MultiCall(queries)
# save raw results
with open('scripts/.callviewtest.json', 'w') as fout:
    json.dump(results, fout)

# new = prep.ViewPrep(results)

# freqs by ttype call TODO build fcrit options from corpinfo call
queries = ("freqs", [{
    "query": '[lemma="test"]',
    "fcrit": fcrit,
    "corpus": "preloaded/ecolexicon_en"
    }])

# freqs line details
queries = ("freqs", [{
    "query":  '[lemma="test"]',
    "fcrit":  'doc 0 s 0',
    "corpus":  "preloaded/ecolexicon_en"
    }])

# wordlist call
queries = ("wordlist", [
    {"attr": "doc.country"}
    ])

# run multiple calls of the same type
queries = ("wordlist", [
    {"attr": "doc.domains", "corpus": "preloaded/ecolexicon_en"},
    {"attr": "class.REGION", "corpus": "user/PilarLeon/hejuly2019_backup"},
    ])

results = callsa.MultiCall(queries)

# TODO add timestamp
# from datetime import datetime
# # get time
# now = datetime.now().strftime("%Y-%m-%d %H.%M.%S")
