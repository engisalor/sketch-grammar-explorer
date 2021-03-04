###
# template for corpus info calls (prerequisite for some other call types)
###

def corpinfo(corpus = "preloaded/ecolexicon_en"):
    query_type = "corp_info?"
    # set parameters
    settings = {
        "corpname": corpus,
        "subcorpora": "1",
        "struct_attr_stats": "1",
    }
    return settings, query_type

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