###
# template for view calls
###

# query = str, CQL rule, e.g., '1:[lemma="climate"] []{1,10} 2:[lemma="change"]'
# qattr = str, "q" or "a", a allows to set the default attr, e.g. 'alemma,1:"gas"'
# randomize = str, "0" (off, default) or "1" 
# pagesize = int, 1<10000, sets the number of concordances retrieved 
# fromp = int, page number returned if multiple
# viewmode = str, "kwic" or "sen" (full sentence, default) 

def view(query, corpus = "preloaded/ecolexicon_en", qattr = 'q', randomize = False, pagesize = 20, fromp = 1, viewmode = "sen", format = "csv"):
    query_type = "view?"
    # randomize
    if randomize == '1':
        rand = "r" + str(pagesize)
    else:
        rand = ""
    # set parameters
    settings = {
        "q": [qattr + query, rand],
        "corpname": corpus,
        "viewmode": viewmode,
        "pagesize": pagesize,
        "fromp": fromp,
        "refs": "doc,s",
        "format": format,
        "asyn": "0",
    }
    return settings, query_type