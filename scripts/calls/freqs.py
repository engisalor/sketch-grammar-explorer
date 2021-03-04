### 
# template for freqs calls 
###

# if fcrit = a list, does a "text types" browser search
# e.g., [x + " 0" for x in ["doc.genre","doc.author"]]
# if fcrit = single string, does a "line details" browser search
# e.g., ["class.DATE 0 class.ID"]

# fcrit = [x + " 0" for x in ttypes]

def freqs(query, fcrit, corpus = "preloaded/ecolexicon_en", format = "csv"):
    query_type = "freqs?"
    # set parameters
    settings = {
        "q": "q" + query,
        "fcrit": fcrit,
        "corpname": corpus,
        "format": format,
        "asyn": "0",
        }
    return settings, query_type