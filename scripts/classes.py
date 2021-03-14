import pathlib
import re
import json
import ast

class Call:
    """
    parent class for all API call types
    """
    data_folder = pathlib.Path("")
    fauth = data_folder / ".auth_api.txt"
    with open(fauth) as f:
        LOGIN = dict(x.rstrip().split(":") for x in f)
  
    def __init__(
        self,
        username = LOGIN["username"],
        api_key = LOGIN["api_key"],
        asyn="0",
        dformat="json"):

        self.username = username
        self.api_key = api_key
        self.asyn = asyn
        self.format = dformat

class Prep:
    """
    format group of calls supplied as a string
    """

    def formatq(self,q,randomize,pagesize,qattr):
        q = re.sub(' +', '', q)
        if randomize is "1":
            r = "r" + str(pagesize)
            q = [qattr + q, r]
            return q
        else:
            q = [qattr + q]
            return q
    
    def FormatCalls(self, clist=None,labels=False):
        if clist is None:
            return [self.__dict__]
        else:
            # get lines
            clist = re.sub(' +', '',clist)
            lines = [x for x in clist.splitlines() if x]
            # convert calls in to dicts
            for x in range(len(lines)):
                try:
                    lines[x] = ast.literal_eval("{" + lines[x] + "}")
                # add labels to calls
                except:
                    # single labels
                    if lines[x][0] == "#" and lines[x][1] != "#":
                        lines[x+1] += ''',"label":"''' + lines[x].strip("# ") + '"'
                    # group labels
                    if lines[x][:3] == "###":
                        stop = [lines[x+1:].index(s) for s in lines[x+1:] if s[0] == "#"]
                        # if a label exists after
                        if len(stop) != 0:
                            for n in range(1,stop[0]+1):
                                lines[x+n] += ''',"label":"''' + lines[x].strip("# ") + '"'
                        # if no labels after
                        if len(stop) == 0:
                            for n in range(x+1,len(lines)):
                                lines[n] += ''',"label":"''' + lines[x].strip("# ") + '"'
            # make formatted clist
            calls = [x for x in lines if type(x) is dict]
            # make a template for each clist call
            formattedcalls = [self.__dict__]*(len(calls)+1)
            # set unique parameters for each extra call
            for x in range(0, len(calls)):
                formattedcalls[x] = {**formattedcalls[x], **calls[x]}
            # format q, add auto label if none
            num = 0
            for x in formattedcalls:
                x["q"] = self.formatq(x["q"],x["randomize"],x["pagesize"],x["qattr"])
                if "label" not in x:
                    x["label"] = "q" + "{:0{y}d}".format(num, y=len(str(len(formattedcalls))))
                    num += 1
                del x["randomize"], x["pagesize"], x["qattr"]

            # split calls and labels
            labels = [x["label"] for x in formattedcalls]
            dicts = [x for x in formattedcalls]
            for x in dicts:
                del x["label"]
            # make calls immutable
            uniquecalls = [json.dumps(x, sort_keys=True) for x in dicts]
            # replace repeated calls with None
            for y in range(len(uniquecalls)):
                reps = []
                if uniquecalls.count(uniquecalls[y]) > 1:
                    uniquecalls[y] = "None"
            # return to mutable
            uniquecalls = [ast.literal_eval(x) for x in uniquecalls]
            drops = []
            # add labels
            for x in range(len(uniquecalls)):
                try:
                    uniquecalls[x]["label"] = labels[x]
                except:
                    drops.append(x)
            # remove None items
            for x in drops:
                del uniquecalls[x]
            return uniquecalls







    # def FormatCalls(self, clist=None):
    #     if clist is None:
    #         return [self.__dict__]
    #     else:
    #         # get lines
    #         clist = re.sub(' +', '',clist)
    #         lines = [x for x in clist.splitlines() if x]
    #         # separate calls from labels
    #         calls = [ast.literal_eval("{" + lines[x] + "}") for x in range(len(lines)) if lines[x][0] != "#"]
    #         # make list identical calls
    #         formattedcalls = [self.__dict__]*(len(calls)+1)
    #         # set unique parameters for each extra call
    #         for x in range(1,len(calls)-1):
    #             formattedcalls[x] = {**formattedcalls[x], **calls[x]}
    #         # remove identical calls
    #         formattedcalls = [json.dumps(x, sort_keys=True) for x in formattedcalls]
    #         formattedcalls = list(set(formattedcalls))
    #         formattedcalls = [ast.literal_eval(x) for x in formattedcalls]
    #         return formattedcalls

    # def MakeCalls(self, formattedcall):
    #     # separate query_type from formattedcall
    #     query_type = formattedcall["query_type"]
    #     del formattedcall["query_type"]
    #     # run request
    #     print("... calling ", query_type, formattedcall)
    #     d = requests.get("https://api.sketchengine.eu/bonito/run.cgi/" + query_type, params=formattedcall)
    #     # parse data
    #     try:
    #         d = d.json()
    #         # errors given in results
    #         if "error" in d:
    #             print("API error:", d["error"])
    #         else:
    #             return d
    #     except:
    #         # other errors
    #         print("API error:", d)

    # def anotherfunc(self, clist):
    #     formatted calls = self.FormatCalls(clist)

class View(Call,Prep):
    """
    set parameters for a View simplecall
    """

    def __init__(
        self,
        q,
        query_type="view?",
        qattr="alemma,",        
        corpname="preloaded/ecolexicon_en",
        randomize=False,
        pagesize=100,
        fromp="1",
        refs="doc,s",
        viewmode="sen",
        ):
        super().__init__()
        self.q = q
        self.query_type = "view?"
        self.qattr = qattr
        self.corpname = corpname
        self.randomize = randomize
        self.pagesize = pagesize
        self.fromp = fromp
        self.refs = refs
        self.viewmode = viewmode
        # del self.qattr, self.randomize


clist = """
"q": ''' "car" '''
### GROUP
"q": ''' "water" '''
"q": ''' "ice" '''

# SINGLE
"q": ''' "pie" '''
"q": ''' "cake" '''

 
"""
parameters = {'q': '"CHEER"','query_type': 'View', 'refs': 'doc,s', 'corpname': 'TEST', 'qattr': 'alemma,', 'viewmode': 'sen', 'randomize': '0', 'pagesize': 100, 'fromp': 1}

# View(**parameters)

formattedcalls = View(**parameters).FormatCalls(clist)
formattedcalls
