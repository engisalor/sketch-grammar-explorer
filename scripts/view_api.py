import requests

#### VIEW API CALL

####
# run a view Sketch Engine API call, where:
# query = str, CQL rule, e.g., '1:[lemma="climate"] []{1,10} 2:[lemma="change"]'
# qattr = str, "q" or "a", a allows to set the default attr, e.g. 'alemma,1:"gas"'
# randomize = str, "0" (off, default) or "1" 
# pagesize = int, 1<10000, sets the number of concordances retrieved 
# fromp = int, page number returned if multiple
# viewmode = str, "kwic" or "sen" (full sentence, default) 
####

# TODO try list of queries w/ ‘q=item1;q=item2…’
# TODO sample and other page size parameters should be separated and improved
# TODO offer other parameter options in comments

def view_api(query, qattr = 'q', randomize = False, pagesize = 20, fromp = 1, viewmode = "sen"):

    # get login credentials
    with open(".auth_api.txt") as f:
        LOGIN = dict(x.rstrip().split(":") for x in f)

    # base url
    base_url = "https://api.sketchengine.eu/bonito/run.cgi/"
    query_type = "view?"

    # randomize
    if randomize == '1':
        rand = "r" + str(pagesize)
    else:
        rand = ""
    
    # set parameters
    data = {
        "q": [qattr + query, rand],
        "corpname": "preloaded/ecolexicon_en",
        "username": LOGIN["username"],
        "api_key": LOGIN["api_key"],
        "viewmode": viewmode,
        "asyn": "0",
        "pagesize": pagesize,
        "fromp": fromp,
        "refs": "doc,s",
        "format": "json",
    }
    # print("... making request ")

    d = requests.get(base_url + query_type, params=data).json()

    # error handling # FIXME show on app  
    if "error" in d:
        print(d["error"])

    return d

# MANUAL USE
# view_api('[lemma="sand"]', randomize=True)
