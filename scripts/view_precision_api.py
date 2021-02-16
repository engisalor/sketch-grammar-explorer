import requests
import numpy as np
import pandas as pd
import time
import re

#### 
####

# get login credentials
with open(".auth_api.txt") as f:
    LOGIN = dict(x.rstrip().split(":") for x in f)

# make url
base_url = "https://api.sketchengine.eu/bonito/run.cgi/"
query_type = "view?"
cql_query = "q" + '[lemma="sand"]'
rand = "r10"
data = {
    "q": [cql_query, rand], 
    # "r": "r200", NOT RIGHT
    # TODO try list of queries w/ ‘q=item1;q=item2…’
    # TODO try getting random sample: r250 instead of q
    "corpname": "preloaded/ecolexicon_en",
    "username": LOGIN["username"],
    "api_key": LOGIN["api_key"],
    "viewmode": "sen", # sen or kwic
    "asyn": "0",
    "pagesize": "20",
    # "attrs": "doc.id,s",
    # "structs": "doc.id,s",
    "refs": "doc,s",
    "format": "json",
}
print("... making request ")
d = requests.get(base_url + query_type, params=data).json()

# save
# np.save("data/view/TEST.npy", d)
# load
# d = np.load('data/view/TEST.npy',allow_pickle='TRUE').item()

# error handling
if "error" in d:
    print(d["error"])

#### PREP DATA

# create df
temp = pd.DataFrame()
for x in d["Lines"]:
    temp = temp.append(pd.DataFrame.from_dict(x, orient="index").T)

# create concordance w bold kwic elements 
for x in range(0, len(d["Lines"])):
    ls = []
    for y in range(0,len(d["Lines"][x]["Kwic"])):
        # add ** around labelled kwic items
        if d["Lines"][x]["Kwic"][y]["class"] == 'col0 coll coll':
            d["Lines"][x]["Kwic"][y]["str"] = "**" + d["Lines"][x]["Kwic"][y]["str"] + "**"
        # combine kwic elements
        ls.append(d["Lines"][x]["Kwic"][y]["str"])
    d["Lines"][x]["fullkwic"] = "".join(ls)
    #combine full conc
    left = "".join([d["Lines"][x]["Left"][y]["str"] for y in range(0,len(d["Lines"][x]["Left"]))])
    right = "".join([d["Lines"][x]["Right"][y]["str"] for y in range(0,len(d["Lines"][x]["Right"]))])
    d["Lines"][x]["conc"] = left + d["Lines"][x]["fullkwic"] + right

# create columns
temp["doc"] = [int(re.sub("\D", "",temp.iloc[x]["Refs"][0])) for x in range(0, len(temp["Refs"]))]
temp["s"] = [int(re.sub("\D", "",temp.iloc[x]["Refs"][1])) for x in range(0, len(temp["Refs"]))]
temp["conc"] = [d["Lines"][x]["conc"] for x in range(0, len(d["Lines"]))]
temp["concsize"] = d["concsize"]
temp["relsize"] = d["relsize"]
temp["#"] = range(0, len(temp))
temp["precise"] = ""

# TODO use md links to go to sketch engine [title](https://www.example.com)

# filter columns
df = temp.filter(["#", "precise", "doc", "s", "conc","concsize","relsize"], axis=1).sort_values(by="s", ascending=True)
