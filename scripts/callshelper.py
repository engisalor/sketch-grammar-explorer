import re
from pathlib import Path
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

###
# get list of different kinds of word sketches in a grammar
###

def getwstypes(grammar = "grammar.txt"):
    # set data paths
    data_folder = Path("")
    fgrammar = data_folder / grammar
    # get grammar file
    with open(fgrammar) as f:
        lines = [line.rstrip() for line in f]
    lines = lines[lines.index("### Pilar's relations start here") :]
    # make list of word sketch types
    wslist = []
    for x in range(0, len(lines)):
        if "%" in lines[x]:
            wslist = wslist + lines[x].split("/")
    # prep word sketch list for API usage
    wslist = ['"' + re.sub('.*" ', ".*", w) + '"' for w in wslist]
    return wslist