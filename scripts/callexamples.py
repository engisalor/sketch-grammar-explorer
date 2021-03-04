import scripts.calls as calls
import scripts.callshelper as helper

###
# API calls of different types and helper functions
###

# get word sketches from a grammar
wstypes = helper.getwstypes()

# GET TTYPES for a corpus
# get corpinfo # TODO
queries = ("corpinfo", [{
    "corpus": "preloaded/ecolexicon_en"
    }])
info = helper.multicall(queries)
# get structs for corpus
# build queries
ls = [{"attr": x} for x in ["info", "for", "structs"]] # TODO
queries = ("wordlist", ls)
# run api calls with structs
results = helper.multicall(queries)
# make df of ttypes, frqs
dfttypes = pd.DataFrame() # TODO for this script or put elsewhere?
dfttypes["struct"] = 0 # list of structs for each type
dfttypes["ttype"] = [results["Items"][x]["str"] for x in range(len(results["Items"]))]
dfttypes["frq"] = [results["Items"][x]["frq"] for x in range(len(results["Items"]))] # TODO


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

### CORP INFO CALL
queries = ("corpinfo", [{
    "corpus": "preloaded/ecolexicon_en"
    }])

### ATTR VALS CALL ***BROKEN***
queries = ("attrvals", [{    
    "avattr": "doc.domains", 
    "avpat": None, 
    "maxitems": 10,
    "corpus": "preloaded/ecolexicon_en"
    }])

### VIEW CALL
queries = ("view", [{
    "query": '[lemma="test"]', 
    "corpus": "preloaded/ecolexicon_en", 
    "qattr": 'q', 
    "randomize": False, 
    "pagesize": 20, 
    "fromp": 1, 
    "viewmode": "sen"
    }])

### FREQS TTYPES CALL TODO build fcrit from corpinfo call
queries = ("freqs", [{
    "query": '[lemma="test"]',
    "fcrit": fcrit,
    "corpus": "preloaded/ecolexicon_en"
    }])

### FREQS LINE DETAILS CALL
queries = ("freqs", [{
    "query":  '[lemma="test"]',
    "fcrit":  'doc 0 s 0',
    "corpus":  "preloaded/ecolexicon_en"
    }])

### WORDLIST CALL
queries = ("wordlist", [
    {"attr": "doc.country"}
    ])

### RUN MULTICALL
queries = ("wordlist", [
    {"attr": "doc.domains", "corpus": "preloaded/ecolexicon_en"},
    {"attr": "class.REGION", "corpus": "user/PilarLeon/hejuly2019_backup"},
    ])

results = helper.multicall(queries)

# TODO # for splitting csv formatted results: f.split("\n")
# TODO add timestamp
# from datetime import datetime
# # get time
# now = datetime.now().strftime("%Y-%m-%d %H.%M.%S")
