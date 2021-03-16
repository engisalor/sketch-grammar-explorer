import pathlib
import re
import json
import ast

class Call:
    """
    parent class for all API call types, with methods needed for building and making calls
    """
 
    def __init__(self,gparams={"asyn":"0", "format":"json"}):
        self.gparams = gparams
        self.creds = self.auth()

    def auth(self, filepath=".auth_api.txt"):
        filepath = pathlib.Path(filepath)
        with open(filepath) as f:
            return dict(x.rstrip().split(":") for x in f)

    def formatc(self):
        if self.clist is None:
            return [self.setq(self.params)]
        else:
            # get lines
            clist = re.sub(' +', '', self.clist)
            lines = [x for x in clist.splitlines() if x]
            # separate calls from labels
            calls = [ast.literal_eval("{" + lines[x] + "}") for x in range(len(lines)) if lines[x][0] != "#"]
            # copy params by clist len
            formatted = [self.params]*(len(calls))
            # set unique parameters for c in clist
            for x in range(len(calls)):
                formatted[x] = {**formatted[x], **calls[x]}
            # set q
            formatted = [self.setq(params) for params in formatted]
            # remove identical calls and NAs
            return [x for x in self.uniquec(formatted) if x]

    def uniquec(self,formatted):
        # make immutable
        immutable = [json.dumps(x, sort_keys=True) for x in formatted]
        # replace repeats with None starting from end
        for y in reversed(range(len(immutable))):
            if immutable.count(immutable[y]) > 1:
                immutable[y] = "None"
        # return to dicts
        return [ast.literal_eval(x) for x in immutable]

    def setq(self,params):
        temp = params.copy()
        q = re.sub(' +', '', params["q"])
        if self.settings["randomize"] is True:
            r = "r" + str(params["pagesize"])
            q = [self.settings["qattr"] + q, r]
            temp["q"] = q
        else:
            q = [self.settings["qattr"] + q]
            temp["q"] = q
        return temp

    def label(self):
        if self.clist is None:
            return None
        else:
        # get lines
        clist = re.sub(' +', '', self.clist)
        lines = [x for x in clist.splitlines() if x]
        # make calls comparable strings
        for x in range(len(lines)):
            if lines[x][0] != "#":
                lines[x] = ast.literal_eval("{" + lines[x] + "}")
                lines[x] = json.dumps(lines[x], sort_keys=True)
        lines = [x for x in Call.uniquec(None,lines) if x]
        # add labels
        for x in range(len(lines)):
            # single labels
            if lines[x][0] == "#" and lines[x][1] != "#":
                lines[x+1] = lines[x].strip("# ")
            # group labels
            if lines[x][:3] == "###":
                stop = [lines[x+1:].index(s) for s in lines[x+1:] if s[0] == "#"]
                # if a label exists after
                if len(stop) != 0:
                    for n in range(1,stop[0]+1):
                        lines[x+n] = lines[x].strip("# ")
                # if no labels after
                if len(stop) == 0:
                    for n in range(x+1,len(lines)):
                        lines[n] = lines[x].strip("# ")
            # if no label
            if lines[x][0] == "{":
                lines[x] = None
        # drop old
        return [x for x in lines if x is None or x[0] != "#"]

class view(Call):
    """
    subclass for view API usage
    """

    def __init__(
        self,
        params = {
            "query_type": "view?",
            "q": None,
            "corpname": "preloaded/ecolexicon_en",
            "pagesize": 100,
            "fromp": "1",
            "refs": "doc,s",
            "viewmode": "sen"},
        settings = {
            "qattr": "alemma,",        
            "randomize": False},
        clist = None):
        super().__init__()
        self.params = params
        self.clist = clist
        self.settings = settings
        self.formatted = self.formatc()
        self.labels = self.label()

clist = """
"q": ''' "car" '''
"q": ''' "water" '''
# SINGLE
"q": ''' "pie" '''
"q": ''' "water" '''
"""

p = {'q': '"water"','refs': 'doc,s', 'corpname': "preloaded/ecolexicon_en", 'viewmode': 'sen', 'pagesize': 100, 'fromp': 1}
s = {"qattr": "alemma,", "randomize": True}

c = view(p,s,clist)