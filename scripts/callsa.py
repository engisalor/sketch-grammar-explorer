import re
import pathlib
import scripts.calls as calls

###
# MultiCall to combine multiple calls of the same query type
###

# queries is a tuple: (call type, list of dicts of variables for each call)
# queries = ("wordlist", [
#     {"attr": "doc.domains"}, # , "corpus": "preloaded/ecolexicon_en"
#     {"attr": "class.REGION", "corpus": "user/PilarLeon/hejuly2019_backup"},
#     ])


def MultiCall(queries):
    print("MULTICALL start")
    results = []
    # make calls and combine results, w/ API throttling
    for x in range(len(queries[1])):
        print("... defining call", str(x))
        query_type, settings = getattr(calls, queries[0])(**queries[1][x])
        temp = calls.BasicCall(query_type, settings)
        results.append(temp)
        calls.wait(len(queries[1]))
    print("MULTICALL done")
    return results


###
# get structures from corpus w/ size
###

# info is made beforehand with corpinfo()
# drops is a list of structs that should be ignored
# maxitems removes structs with too many values
# (SkE may force a limit of 1000 on some corpora)


def Structs(info, drops=[], maxitems=500):
    dt = {}
    for y in range(len(info[0]["structs"])):
        # get main structs
        dt[info[0]["structs"][y][0]] = info[0]["structs"][y][1]
        # get struct ttypes
        for x in range(len(info[0]["structs"][y][2])):
            dt[info[0]["structs"][y][2][x][0]] = info[0]["structs"][y][2][x][2]
    # run numeric filter
    dt = dict((k, v) for k, v in dt.items() if v <= maxitems)
    # run string filter
    if drops:
        if drops is str:
            drops = [drops]
        dt = dict((k, v) for k, v in dt.items() if k not in drops)
    # return
    return dt


###
# get word sketch types in a grammar
###

# supply a text file with the same format as the EcoLexicon Semantic Sketch Grammar
# TODO this should be made more flexible for other corpora


def WStypes(grammar="grammar.txt"):
    # set data paths
    data_folder = pathlib.Path("")
    fgrammar = data_folder / "grammar.txt"
    # get grammar file
    with open(fgrammar) as f:
        lines = [line.rstrip() for line in f]
    lines = lines[lines.index("### Pilar's relations start here") :]
    # make list of word sketch types
    wstypes = []
    for x in range(0, len(lines)):
        if "%" in lines[x]:
            wstypes = wstypes + lines[x].split("/")
    # prep word sketch list for API usage
    wstypes = ['"' + re.sub('.*" ', ".*", w) + '"' for w in wstypes]
    wstypes = ['[ws(".*-n",' + x + ',".*-n")]' for x in wstypes]
    # make dict of wstypes and cql
    dt = {}
    for x in range(len(wstypes)):
        key = re.search(r",\"\.\*(.+)\.\.\.", wstypes[x]).group(1)
        dt[key] = wstypes[x]
    return dt
