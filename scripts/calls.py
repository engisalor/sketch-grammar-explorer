from requests import get
from pathlib import Path
from time import sleep

###
# attrvals call ***BROKEN*** gets response but "suggestions" always empty
###

def attrvals(
    avattr,
    avpat = None, 
    maxitems = 10, 
    corpus = "preloaded/ecolexicon_en", 
    rformat = "json"):
    query_type = "attr_vals?"
    # set parameters
    settings = {
        "avattr": avattr,
        "avpat": avpat,
        "avmaxitems":maxitems,
        "corpname": corpus,
        "format": rformat,
        }
    return query_type, settings

###
# BasicCall for any API call
###

# all SkE API call types are fed through this function
# requires a text file w/ API credentials
# parsing data from multiple formats is possible (txt instead of json) 
# but downstream functions so far only accept json
# querytype = name of api call function, e.g., "freqs", "corpinfo", "wordlist"
# settings = dict of parameters required for that api call--see each function 

def BasicCall(
    query_type,
    settings,
    ):
    # set file paths
    data_folder = Path("")
    fauth = data_folder / ".auth_api.txt"
    # get login credentials
    with open(fauth) as f:
        LOGIN = dict(x.rstrip().split(":") for x in f)
    # combine parameters
    data = {
        "username": LOGIN["username"],
        "api_key": LOGIN["api_key"],
        "asyn": "0",
    }
    alldata = {**data, **settings}
    # run request
    # print("MAKING REQUEST")
    print("... calling ", query_type) # , "...",settings
    d = get("https://api.sketchengine.eu/bonito/run.cgi/" + query_type, params=alldata)
    # parse data
    # print("... parsing")
    try:
        d = d.json()
        # print("... found json format")
        # errors
        if "error" in d:
            print("API error:", d["error"])
        else:
            # print("DONE")
            return d
    except:
        print("API error:", d)

###
# corpinfo call
###

def corpinfo(corpus = "preloaded/ecolexicon_en"):
    query_type = "corp_info?"
    # set parameters
    settings = {
        "corpname": corpus,
        "subcorpora": "1",
        "struct_attr_stats": "1",
    }
    return query_type, settings

### 
# freqs call 
###

# if fcrit = a list, does a "text types" browser search
# e.g., [x + " 0" for x in ["doc.genre","doc.author"]]
# if fcrit = single string, does a "line details" browser search
# e.g., ["class.DATE 0 class.ID"]

def freqs(query, fcrit, corpus = "preloaded/ecolexicon_en", rformat = "json"):
    query_type = "freqs?"
    # set parameters
    settings = {
        "q": "q" + query,
        "fcrit": fcrit,
        "corpname": corpus,
        "format": rformat,
        "asyn": "0",
        }
    return query_type, settings

###
# view call
###

# query = str, CQL rule, e.g., '1:[lemma="climate"] []{1,10} 2:[lemma="change"]'
# qattr = str, "q" or "a", a allows to set the default attr, e.g. 'alemma,1:"gas"'
# randomize = str, "0" (off, default) or "1" 
# pagesize = int, 1<10000, sets the number of concordances retrieved 
# fromp = int, page number returned if multiple
# viewmode = str, "kwic" or "sen" (full sentence, default)
# refs = str, "doc,s,etc." NO spaces allowed

def view(query, corpus = "preloaded/ecolexicon_en", qattr = 'q', randomize = '0', pagesize = 100, fromp = 1, viewmode = "sen", refs = "doc,s", rformat = "json"):
    query_type = "view?"
    # randomize
    if randomize == '1':
        rand = "r" + str(pagesize)
    else:
        rand = ""
    # set parameters
    settings = {
        "q": [qattr + query, rand],
        "corpname": corpus,
        "viewmode": viewmode,
        "pagesize": pagesize,
        "fromp": fromp,
        "refs": refs,
        "format": rformat,
        "asyn": "0",
    }
    return query_type, settings


###
# wait - throttles API usage for multiple calls
###

def wait(n):
    if type(n) is int and n > 0:
        # set API wait
        if n < 100:
            wait = 1
        elif 100 <= n < 900:
            wait = 4
        elif 900 < n:
            wait = 45
        # wait
        print("... waiting ", str(wait))
        sleep(wait)
    else:
        print("WAIT error")

### 
# wordlist call (total frqs for a text type) 
###

def wordlist(attr, corpus = "preloaded/ecolexicon_en", rformat = "json", maxitems = 1000):
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
    return query_type, settings