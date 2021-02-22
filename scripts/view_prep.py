import pandas as pd
import re

#### VIEW API PREP DATA

####
# preprocess a view Sketch Engine API call, where:
# d = JSON-formatted API data
# version = Sketch Grammar Explorer version number
####

def view_prep(d, version = "unknown"):

    # create temp
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

    # create df
    df = pd.DataFrame()
    df["#"] = range(0, len(temp))
    df["precise"] = ""
    df["doc"] = [int(re.sub("\D", "",temp.iloc[x]["Refs"][0])) for x in range(0, len(temp["Refs"]))]
    df["s"] = [int(re.sub("\D", "",temp.iloc[x]["Refs"][1])) for x in range(0, len(temp["Refs"]))]
    df["conc"] = [d["Lines"][x]["conc"] for x in range(0, len(d["Lines"]))]
    df["concsize"] = d["concsize"]
    df["relsize"] = d["relsize"]
    df["version"] = version

    return df