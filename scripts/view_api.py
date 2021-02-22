import requests

#### VIEW API CALL

####
# run a view Sketch Engine API call, where:
# query = str, CQL rule, e.g., '1:[lemma="climate"] []{1,10} 2:[lemma="change"]'
# random = boolean, True/False 
# sample = integer (sets sample size whether or not it's randomized)
####

# TODO try list of queries w/ ‘q=item1;q=item2…’
# TODO sample and other page size parameters should be separated and improved
# TODO offer other parameter options in comments

def view_api(query, random = False, sample = 500):

    # get login credentials
    with open(".auth_api.txt") as f:
        LOGIN = dict(x.rstrip().split(":") for x in f)

    # base url
    base_url = "https://api.sketchengine.eu/bonito/run.cgi/"
    query_type = "view?"

    # random sample
    if random == True:
        rand = "r" + str(sample)
    else:
        rand = ""
    
    # set parameters
    data = {
        "q": ["q" + query, rand], 
        "corpname": "preloaded/ecolexicon_en",
        "username": LOGIN["username"],
        "api_key": LOGIN["api_key"],
        "viewmode": "sen", # sen or kwic
        "asyn": "0",
        "pagesize": sample,
        # "attrs": "",
        # "structs": "",
        "refs": "doc,s",
        "format": "json",
    }
    print("... making request ")

    d = requests.get(base_url + query_type, params=data).json()

    # error handling  
    if "error" in d:
        print(d["error"])

    return d