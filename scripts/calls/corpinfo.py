import requests
import re
import json
from pathlib import Path

###
# template for corpus info calls (prerequisite for some other call types)
###

def corpinfo(save = False, corpus = "preloaded/ecolexicon_en"):
    # set file paths
    data_folder = Path("")
    fauth = data_folder / ".auth_api.txt"
    fpath = data_folder / "data/"

    # get authentication pairs
    with open(fauth) as f:
        LOGIN = dict(x.rstrip().split(":") for x in f)

    # define request
    base_url = "https://api.sketchengine.eu/bonito/run.cgi/"
    query_type = "corp_info?"
    data = {
        "subcorpora": "1",
        "struct_attr_stats": "1",
        "corpname": corpus,
        "username": LOGIN["username"],
        "api_key": LOGIN["api_key"],
        "async": "0",
        "format": "json",
    }

    # get data
    print("\nMAKING CALL")
    print("...calling ", corpus)
    d = requests.get(base_url + query_type, params=data).json()

    # errors
    if "error" in d:
        print("API error: ", d["error"])

    # save
    elif save:
        print("...saving file")
        fname = "corpinfo " + re.search(r'/([^/]+)$', corpus).group(1) + ".json"
        with open(fpath / fname, "w") as file:
            json.dump(d, file)
        print("DONE\n")

    # return
    else:

        # TODO extract corpus data for visualization/piping to other calls
        # # get corpus structures
        # dt = {}
        # for y in range(len(d["structs"])):
        #     for x in range(len(d["structs"][y][2])):
        #         dt[d["structs"][y][2][x][0]] = d["structs"][y][2][x][2]
        # # set text types
        # if d["request"]["corpname"] == "user/PilarLeon/hejuly2019_backup":
        #     for x in ["doc.id","doc.filename","doc.wordcount"]: 
        #         dt.pop(x)
        # if d["request"]["corpname"] == "preloaded/ecolexicon_en":
        #     for x in ["doc.author","doc.keywords","doc.title","doc.wordcount"]: 
        #         dt.pop(x)
        # ttypes = list(dt.keys())    

        print("DONE\n")
        return d