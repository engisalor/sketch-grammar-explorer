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
            temp = self.params.copy()
            q = re.sub(' +', '', temp["q"])
            if self.settings["randomize"] is True:
                r = "r" + str(temp["pagesize"])
                q = [self.settings["qattr"] + q, r]
            else:
                q = [self.settings["qattr"] + q]
            temp["q"] = q
            return [temp]
        else:
            # get lines
            clist = re.sub(' +', '', self.clist)
            lines = [x for x in clist.splitlines() if x]
            # separate calls from labels
            calls = [ast.literal_eval("{" + lines[x] + "}") for x in range(len(lines)) if lines[x][0] != "#"]
            # copy params * len(clist)
            formattedcalls = [self.params]*(len(calls)+1)
            # set unique parameters for each c in clist
            for x in range(len(calls)):
                formattedcalls[x] = {**formattedcalls[x], **calls[x]}
            # set q
            for params in formattedcalls:
                temp = params.copy()
                q = re.sub(' +', '', temp["q"])
                if self.settings["randomize"] is True:
                    r = "r" + str(temp["pagesize"])
                    q = [self.settings["qattr"] + q, r]
                else:
                    q = [self.settings["qattr"] + q]
                params["q"] = q
            # remove identical calls
            return self.uniquec(formattedcalls)

    def uniquec(self,formattedcalls):
        # make immutable
        immutable = [json.dumps(x, sort_keys=True) for x in formattedcalls]
        # replace repeats with None 
        for y in range(len(immutable)):
            reps = []
            if immutable.count(immutable[y]) > 1:
                immutable[y] = "None"
        # return to dicts
        immutable = [ast.literal_eval(x) for x in immutable]
        return immutable

    # def setq(self,params): # FIXME function breaks after second try in terminal
    #     q = re.sub(' +', '', params["q"])
    #     if self.settings["randomize"] is True:
    #         r = "r" + str(params["pagesize"])
    #         q = [self.settings["qattr"] + q, r]
    #         return q
    #     else:
    #         q = [self.settings["qattr"] + q]
    #         return q

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

# """
params = {'q': '"water"','refs': 'doc,s', 'corpname': "preloaded/ecolexicon_en", 'viewmode': 'sen', 'pagesize': 100, 'fromp': 1}
settings = {"qattr": "alemma,", "randomize": True}

c = view(params,settings,clist)
c.formatted