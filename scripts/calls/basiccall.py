from requests import get
from pathlib import Path
###
# basic format for API calls using templates
###

def basiccall(
    query_type,
    settings,
    corpus = "preloaded/ecolexicon_en", 
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
    print("\n\nMAKING REQUEST")
    print("... calling ", query_type, "\n...",settings)
    d = get("https://api.sketchengine.eu/bonito/run.cgi/" + query_type, params=alldata)

    # parse data
    print("... parsing")
    try:
        d = d.json()
        print("... found json format")
        # errors
        if "error" in d:
            print("API error: ", d["error"])
        else:
            print("DONE\n")
            return d
    except:
        try:
            d = d.text
            print("... found csv format")
            # errors
            if "corpus" not in d:
                print("API error: can't parse data\n", d, "\nDONE\n")
            else:
                print("DONE\n")
                return d
        except:
            print("API error: unknown\n", d, "\nDONE\n")