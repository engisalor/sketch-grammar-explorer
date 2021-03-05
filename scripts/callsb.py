import scripts.calls as calls
import scripts.callsa as callsa

###
# get records of text types and their frequencies in a corpus
###

# makes a corpinfo() call and a Structs() call to supply data
# output is record format for immediate use with Dash datatable

def TTypes(queries, drops = [], maxitems = 500):
    info = callsa.MultiCall(queries)
    structs = callsa.Structs(info, drops, maxitems)
    # build queries
    queries = ("wordlist", [{"attr": x, "corpus": info[0]["request"]["corpname"]} for x in structs.keys()])
    # run api calls with structs
    results = callsa.MultiCall(queries)
    # combine results into records
    for y in range(len(results)):
        # get current struct
        struct = results[y]["request"]["wlattr"]
        # add struct to each entry
        for x in range(len(results[y]["Items"])):
            results[y]["Items"][x]["struct"] = struct
    records = [results[x]["Items"][y] for x in range(len(results)) for y in range(len(results[x]["Items"]))]
    # return
    return records