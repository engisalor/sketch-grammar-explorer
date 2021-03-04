import scripts.calls as calls

###
# multicall to combine multiple calls of the same query type
###

# queries is a tuple: (call type, list of dicts of variables for each call)
# queries = ("wordlist", [
#     {"attr": "doc.domains"}, # , "corpus": "preloaded/ecolexicon_en"
#     {"attr": "class.REGION", "corpus": "user/PilarLeon/hejuly2019_backup"},
#     ])

def multicall(queries):
    print("\nSTARTING MULTICALL")
    results = []
    # make calls and combine results, w/ API throttling
    for x in range(len(queries[1])):
        print("... defining call", str(x))
        query_type, settings = getattr(calls,queries[0])(**queries[1][x])
        temp = calls.basiccall(query_type, settings)
        results.append(temp)
        calls.wait(len(queries[1]))
    print("DONE\n")
    return results