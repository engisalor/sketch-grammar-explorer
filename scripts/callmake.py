import scripts.calls as calls
from scripts.multicall import multicall

###
# run API calls of different types and return results
###

### CORP INFO CALL
query_type, settings = calls.corpinfo()

### ATTR VALS CALL ***BROKEN***
query_type, settings = calls.attrvals(
    avattr = "doc.domains", 
    # avpat = None, 
    # maxitems = 10,
    # corpus = "preloaded/ecolexicon_en"
    )

### VIEW CALL
query_type, settings = calls.view(
    query = '[lemma="test"]', 
    corpus = "preloaded/ecolexicon_en", 
    qattr = 'q', 
    randomize = False, 
    pagesize = 20, 
    fromp = 1, 
    viewmode = "sen"
    )

### FREQS CALL TODO build fcrit from corpinfo/wordlist call
query_type, settings = calls.freqs(
    query = '[lemma="test"]',
    fcrit = fcrit,
    corpus = "preloaded/ecolexicon_en")

### FREQS HITS PER DOC / SENTENCE CALL
query_type, settings = calls.freqs(
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

### WORDLIST CALL
query_type, settings = calls.wordlist("doc.country") # e.g., "class.REGION", "user/PilarLeon/hejuly2019_backup"

### RUN BASICCALL
f = calls.basiccall(query_type,settings)

### RUN MULTICALL 
queries = ("wordlist", [
    {"attr": "doc.domains", "corpus": "preloaded/ecolexicon_en"},
    {"attr": "class.REGION", "corpus": "user/PilarLeon/hejuly2019_backup"},
    ])
results = multicall(queries)

# for getting text type values from wordlist: [f["Items"][x]["str"] for x in range(len(f["Items"]))]
# for splitting csv formatted results: f.split("\n")

# TODO add timestamp
# from datetime import datetime
# # get time
# now = datetime.now().strftime("%Y-%m-%d %H.%M.%S")
