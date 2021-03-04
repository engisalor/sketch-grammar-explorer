### 
# template for attrvals calls ***BROKEN*** gets response but "suggestions" always empty
###

def attrvals(avattr, avpat = None, maxitems = 10, corpus = "preloaded/ecolexicon_en", format = "json"):
    query_type = "attr_vals?"
    # set parameters
    settings = {
        "avattr": avattr,
        "avpat": avpat,
        "avmaxitems":maxitems,
        "corpname": corpus,
        "format": format,
        }
    return settings, query_type