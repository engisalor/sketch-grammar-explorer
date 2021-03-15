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
            # copy params * len(clist)
            formatted = [self.params]*(len(calls)+1)
            # set unique parameters for c in clist
            for x in range(len(calls)):
                formatted[x] = {**formatted[x], **calls[x]}
            # set q
            formatted = [self.setq(params) for params in formatted]
            # remove identical calls
            return self.uniquec(formatted)

    def uniquec(self,formatted):
        # make immutable
        immutable = [json.dumps(x, sort_keys=True) for x in formatted]
        # replace repeats with None 
        for y in range(len(immutable)):
            reps = []
            if immutable.count(immutable[y]) > 1:
                immutable[y] = "None"
        # return to dicts
        immutable = [ast.literal_eval(x) for x in immutable]
        return immutable

    def setq(self,params):
        temp = params.copy()
        q = re.sub(' +', '', params["q"])
        if self.settings["randomize"] is True:
            r = "r" + str(params["pagesize"])
            q = [self.settings["qattr"] + q, r]
            temp["q"] = q
            return temp
        else:
            temp["q"] = q
            q = [self.settings["qattr"] + q]
            return temp

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

clist = """
"q": ''' "car" '''
### GROUP
"q": ''' "water" '''
# SINGLE
"q": ''' "pie" '''
"q": ''' "water" '''
# """
p = {'q': '"water"','refs': 'doc,s', 'corpname': "preloaded/ecolexicon_en", 'viewmode': 'sen', 'pagesize': 100, 'fromp': 1}
s = {"qattr": "alemma,", "randomize": True}

c = view(p,s,clist)
c.formatted