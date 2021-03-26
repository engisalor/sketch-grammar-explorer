import requests
import pathlib
import time
import ast
import re
import json

###
# attrvals call ***BROKEN*** gets response but "suggestions" always empty
###


def attrvals(
    avattr, avpat=None, maxitems=10, corpus="preloaded/ecolexicon_en", rformat="json"
):
    query_type = "attr_vals?"
    # set parameters
    settings = {
        "avattr": avattr,
        "avpat": avpat,
        "avmaxitems": maxitems,
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


def BasicCall(parameters):
    # separate querytype from parameters
    query_type = parameters["querytype"]
    del parameters["querytype"]
    # set file paths
    data_folder = pathlib.Path("")
    fauth = data_folder / ".auth_api.txt"
    # add credentials
    with open(fauth) as f:
        LOGIN = dict(x.rstrip().split(":") for x in f)
    credentials = {
        "username": LOGIN["username"],
        "api_key": LOGIN["api_key"],
        "asyn": "0",
        "format": "json",
    }
    parameters.update(credentials)
    # run request
    print("... calling ", query_type)
    d = requests.get(
        "https://api.sketchengine.eu/bonito/run.cgi/" + query_type, params=parameters
    )
    # parse data
    try:
        d = d.json()
        # errors given in results
        if "error" in d:
            print("API error:", d["error"])
        else:
            return d
    except:
        # other errors
        print("API error:", d)


###
# corpinfo call
###


def corpinfo(corpus="preloaded/ecolexicon_en"):
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


def freqs(query, fcrit, corpus="preloaded/ecolexicon_en", rformat="json"):
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
# ParseCallList: parse a string containing at least one call
###

# GENERAL
# always be sure a call is valid before using the API
# after too many failed attempts your API key can be deactivated by the SkE server
# (usually for the rest of the day, in my experience)
# if a key is not specified, the default value is used (as set with the interface)
# any combination of API calls is possible, but not necessarily advisable
# e.g., specifying different viewmodes or mixing sequential and randomized calls is bad
# unforeseen combinations may throw errors

# LABELS
# a line starting with "#" becomes the label for the following call
# a line starting with "###" becomes the label for every following call (until the next label)
# queries without labels are assigned a numerical one, e.g., "q01", "q02", etc.
# don't use spaces in labels, use dashes or underscores instead

# SYNTAX
# each API call must be on a single line (text wrapping is okay for very long calls)
# empty lines and extra spaces are permissible (extra spaces are encouraged for readability)
# API calls consist of be dictionary key:value pairs: 'key1':'value1', 'key2':'value2'
# use commas between key:value pairs
# no initial/ending brackets are necessary
# keys can be any valid parameters, e.g., "query", "corpus", 'refs'
# keys and most values can be surrounded by single or double quotes
# "query" values must be surrounded by triple quotes ''' [word="water's"]  '''

# EXAMPLE:
clist = """
"query":    '''   1:[  word  =  "ocean's"  ]   '''

# single-label
'query': '''  1:"  fish  "'''  , 'viewmode': "kwic", "corpus": "a different corpus"

### group-label
'fromp  '  :  1
'fromp':2
'fromp':3
"""


def ParseCallList(clist, parameters):
    # get lines
    clist = re.sub(" +", "", clist)
    lines = clist.splitlines()
    lines = [x for x in lines if x]
    # separate rules from labels
    rules = [
        [x, ast.literal_eval("{" + lines[x] + "}")]
        for x in range(len(lines))
        if lines[x][0] != "#"
    ]
    # set labels
    labels = lines[:]
    for x in range(len(lines)):
        # single labels
        if lines[x][0] == "#" and lines[x][1] != "#":
            labels[x + 1] = lines[x]
        # group labels
        if labels[x][:3] == "###":
            stop = [labels[x + 1 :].index(s) for s in labels[x + 1 :] if s[0] == "#"]
            # if a label exists after
            if len(stop) != 0:
                for n in range(0, stop[0] + 1):
                    labels[x + n] = labels[x]
            # if no labels after
            if len(stop) == 0:
                for n in range(x, len(lines)):
                    labels[n] = labels[x]
    # finish labels
    for x in range(len(rules)):
        rules[x][0] = labels[rules[x][0]]
        # add auto labels
        if rules[x][0][0] != "#":
            rules[x][0] = "q" + "{:0{y}d}".format(x + 1, y=len(str(len(rules))))
        # clean all labels
        rules[x][0] = rules[x][0].strip("#")
    # copy parameters for len(clist)
    parameters = [parameters] * len(rules)
    # update unique parameters for each item
    for x in range(len(rules)):
        parameters[x] = {**parameters[x], **rules[x][1]}
        # parameters [x]["hash"] = hash(json.dumps(parameters[x], sort_keys=True)) # can add if needed
    return parameters


###
# view call
###

# query = str, CQL rule, e.g., '1:[lemma="climate"] []{1,10} 2:[lemma="change"]'
# qattr = str, "q" or "a", a allows to set the default attr, e.g. 'alemma,1:"gas"'
# randomize = str, "0" (off, default) or "1"
# pagesize = int, 1<10000, sets the number of concordances retrieved
# fromp = int, page number returned if multiple (starts at 1)
# viewmode = str, "kwic" or "sen" (full sentence, default)
# refs = str, "doc,s,etc." NO spaces allowed


def view(
    query,
    corpus="preloaded/ecolexicon_en",
    qattr="q",
    randomize="0",
    pagesize=100,
    fromp=1,
    viewmode="sen",
    refs="doc,s",
    rformat="json",
):
    query_type = "view?"
    # randomize
    if randomize == "1":
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
        elif 900 <= n:
            wait = 45
        # wait
        print("... waiting ", str(wait))
        time.sleep(wait)
    else:
        print("WAIT error")


###
# wordlist call (total frqs for a text type)
###


def wordlist(attr, corpus="preloaded/ecolexicon_en", rformat="json", maxitems=1000):
    query_type = "wordlist?"
    # set parameters
    settings = {
        "corpname": corpus,
        "wlattr": attr,
        "wlmaxitems": maxitems,
        "wltype": "simple",
        "format": "json",
        "wlsort": "frq",
        "subcnorm": "frq",
        "usesubcorp": "",
        "wlpat": ".*",
        "wlminfreq": 1,
        "wlicase": 1,
        "wlmaxfreq": 0,
        "wlfile": "",
        "wlblacklist": "",
        "wlnums": "",
        "include_nonwords": 1,
        "wlstruct_attr1": "",
        "wlstruct_attr2": "",
        "wlstruct_attr3": "",
        "random": 0,
        "relfreq": 1,
        "reldocf": 1,
        "wlpage": 1,
    }
    return query_type, settings
