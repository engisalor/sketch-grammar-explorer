###
# ViewPrep: creates a list of dicts from multicall view queries
###

def ViewPrep(results):
    print("PREP start")
    e = 0
    # for each line in each query
    for x in range(len(results)):
        for y in range(len(results[x]["Lines"])):
            try:
                # flatten L & R, or convert to string if empty 
                if results[x]["Lines"][y]["Left"]:
                    results[x]["Lines"][y]["Left"] = results[x]["Lines"][y]["Left"][0]["str"]
                else:
                    results[x]["Lines"][y]["Left"] = ""
                if results[x]["Lines"][y]["Right"]:
                    results[x]["Lines"][y]["Right"] = results[x]["Lines"][y]["Right"][0]["str"]
                else:
                    results[x]["Lines"][y]["Left"] = ""
            except:
                e += 1
                print("...", x,y,"skip flatten Left, Right")
            try:
                # add markdown formatting to kwic items
                for z in range(len(results[x]["Lines"][y]["Kwic"])):
                    if results[x]["Lines"][y]["Kwic"][z]["class"] == "col0 coll coll":
                        results[x]["Lines"][y]["Kwic"][z]["str"] = "**" + results[x]["Lines"][y]["Kwic"][z]["str"] + "**"
            except:
                e += 1
                print("...", x,y, "skip add formatting")
            try:
                # combine kwic items and make conc
                results[x]["Lines"][y]["Kwic"] = "".join([results[x]["Lines"][y]["Kwic"][w]["str"] for w in range(len(results[x]["Lines"][y]["Kwic"]))])
                results[x]["Lines"][y]["conc"] = results[x]["Lines"][y]["Left"] + results[x]["Lines"][y]["Kwic"] + results[x]["Lines"][y]["Right"]
            except:
                e += 1
                print("...", x,y, "skip make conc")
            try:
                # flatten refs
                refkeys = results[0]["request"]["refs"].split(",")
                for k in range(len(refkeys)):
                    results[x]["Lines"][y][refkeys[k]] = results[x]["Lines"][y]["Refs"][k]
            except:
                e += 1
                print("...", x,y, "skip flatten refs")
            try:
                # drop items
                drops = ["Left", "Right", "Kwic", "Refs", "toknum", "hitlen", "Tbl_refs","Links", "linegroup", "linegroup_id"]
                for d in drops:
                    del results[x]["Lines"][y][d]
            except:
                e += 1
                print("...", x,y, "skip: drop items")
            try:
                # add items
                results[x]["Lines"][y]["corpus"] = results[x]["request"]["corpname"] # FIXME get final substring "/." 
                results[x]["Lines"][y]["concsize"] = results[x]["concsize"]
                results[x]["Lines"][y]["conc#"] = y
                results[x]["Lines"][y]["q"] = str(results[x]["q"])
            except:
                e += 1
                print("...", x,y, "skip add items")
    print("PREP done:", e, "errors detected")
    return [results[x]["Lines"][y] for x in range(len(results)) for y in range(len(results[x]["Lines"]))]