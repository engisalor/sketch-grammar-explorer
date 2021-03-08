###
# ReadQueries: read a string containing at least one query
###

# TODO works, but needs systematic testing/debugging

# note: always be sure a query is valid before using the API
# after too many failed attempts your API key can be deactivated by the SkE server
# (usually for the rest of the day, in my experience)

# each query must be on a single line (text wrapping is okay for very long queries)
# empty lines and extra spaces are permissible (extra spaces are encouraged for readability)
# queries can be labelled using # to start the previous line, e.g.: # label \n "query": '[lemma="query"]'
# queries without labels are assigned a numerical one, e.g., "q1", "q2", etc.
# FIXME add query labels column
# queries must be written as valid dictionary key:value pairs
# e.g. 'key1':'value1', 'key2':'value2' (surrounding brackets are added automatically)
# keys can be any valid parameters, e.g., "query", "corpus", 'refs'
# any combination of API calls is possible, but not necessarily advisable
# keys and non-query values can be surrounded by single or double quotes
# "query" values must be surrounded by triple quotes ''' '''
# if a key is not specified, the default value is used (as set with the interface)

# example:

"""
"query":    '''   1:[word="ocean's"]   '''
#label
'query': '''1:"fish"'''  , 'viewmode': "kwic", "corpus": "a different corpus"
"""

# many possible combinations are not advisable:
# e.g., specifying different viewmodes or mixing sequential and randomized calls
# some unforeseen combinations may throw errors

def ReadQueries(qstr):
    # get lines
    lines = qstr.splitlines()
    lines = [x for x in lines if x]
    # separate rules from labels, process each
    rules = [[x, eval("{" + lines[x] + "}")] for x in range(len(lines)) if lines[x][0] != "#"]
    labels = [[x+1, lines[x].strip("# ")] for x in range(len(lines)) if lines[x][0] == "#"]
    # recombine labels and rules
    for x in range(len(rules)):
        for y in range(len(labels)):
            if rules[x][0] == labels[y][0]:
                rules[x][0] = labels[y][1]
        if type(rules[x][0]) is int:
            rules[x][0] = "q" + str(rules[x][0])
    return rules

###
# ViewPrep: creates a list of dicts from multicall view queries
###

def ViewPrep(results):
    print("PREP start")
    e = 0
    # for each line in each query
    for x in range(len(results)):
        # get query details
        corpus = results[x]["request"]["corpname"][results[x]["request"]["corpname"].rfind("/")+1:]
        concsize = results[x]["concsize"]
        query = str(results[x]["q"])
        # modify lines
        for y in range(len(results[x]["Lines"])):
            try:
                # flatten L & R, or convert to string if empty
                for s in ["Left", "Right"]: 
                    if results[x]["Lines"][y][s]:
                        results[x]["Lines"][y][s] = results[x]["Lines"][y][s][0]["str"]
                    else:
                        results[x]["Lines"][y][s] = ""
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
                results[x]["Lines"][y]["corpus"] = corpus
                results[x]["Lines"][y]["concsize"] = concsize
                results[x]["Lines"][y]["conc#"] = y
                results[x]["Lines"][y]["q"] = query
            except:
                e += 1
                print("...", x,y, "skip add items")
    print("PREP done:", e, "errors detected")
    return [results[x]["Lines"][y] for x in range(len(results)) for y in range(len(results[x]["Lines"]))]