import pathlib
import re
import json
import ast
import requests
import time
from datetime import datetime
import subprocess
import hashlib
import pandas as pd

import scripts.callsprep as prep

class Call:
    """
    parent class for all API call types, with methods needed for building and making calls
    """
 
    def __init__(self,gparams={"asyn":"0", "format":"json"}):
        self.gparams = gparams
        self.creds = self.auth()
        self.version = self.version()

    def auth(self, filepath=".auth_api.txt"):
        filepath = pathlib.Path(filepath)
        with open(filepath) as f:
            return dict(x.rstrip().split(":") for x in f)

    def version(self):                # get version
        try:
            v = subprocess.check_output(["git", "describe",  "--always"]).decode("utf-8").strip()
            vdate = subprocess.check_output(["git", "show", "-s", "--format=%cd", "--date=short"]).decode("utf-8").strip()
            version = "{} / {}".format(vdate, v)
        except:
            version= "unknown"
        return version

    def format(self):
        if self.clist is None:
            return [self.setq(self.params)]
        else:
            # get lines
            clist = re.sub(' +', '', self.clist)
            lines = [x for x in clist.splitlines() if x]
            # separate calls from labels
            # TODO interpret brackets if already exist
            calls = [ast.literal_eval("{" + lines[x] + "}") for x in range(len(lines)) if lines[x][0] != "#"]
            # copy params by clist len
            formatted = [self.params]*(len(calls))
            # set unique parameters for c in clist
            for x in range(len(calls)):
                formatted[x] = {**formatted[x], **calls[x]}
            # set q
            formatted = [self.setq(params) for params in formatted]
            # remove identical calls and NAs
            return [x for x in self.unique(formatted) if x]

    def unique(self,formatted):
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
            return [None]
        else:
            # get lines
            clist = re.sub(' +', '', self.clist)
            lines = [x for x in clist.splitlines() if x]
            # make calls comparable strings
            for x in range(len(lines)):
                if lines[x][0] != "#":
                    lines[x] = ast.literal_eval("{" + lines[x] + "}")
                    lines[x] = json.dumps(lines[x], sort_keys=True)
            lines = [x for x in self.unique(lines) if x]
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

    def setwait(self):
        # set wait time
        n = len(self.formatted)
        if n == 1:
            wait = 0
        elif 2 <= n < 100:
            wait = 1
        elif 100 <= n < 900:
            wait = 4
        elif 900 <= n:
            wait = 45
        return wait

    def dryrun(self,cache=None):
        print("DRYRUN")
        print("... call type:", self.calltype)
        print("... timestamp:",self.timestamp)
        print("... version:",self.version)
        print("... calls:", len(self.formatted))
        print("... wait:", self.wait)
        print("... creds:",self.creds["username"],"/", self.creds["api_key"][0:5] + "...")
        print("... cache:", cache)
        print("... global parameters:", self.gparams)
        for x in range(len(self.formatted)):
            print("... call{}:".format(str(x)), self.formatted[x])

    def makecalls(self,cache=None,cacheIDs=None,dryrun=False):
        # show dry run details
        if dryrun is True:
            self.dryrun(cache)
        # run each call
        else:
            print("CALL start")
            # no cache
            if cache is None:
                for x in range(len(self.formatted)):
                    d = self.trycall(x)
                    self.results.append(d)
            # use cache
            else:
                # make cacheIDs if empty
                if cacheIDs is None:
                    cacheIDs = []
                for x in range(len(self.formatted)):
                    # make callid
                    temp = json.dumps(self.formatted[x], sort_keys=True)
                    callID = {"hash": str(hashlib.blake2s(temp.encode()).hexdigest()), "call": temp}
                    # skip call if in cache
                    if callID["hash"] in [x["hash"] for x in cacheIDs]:
                        print("... skipping", callID["call"])
                    # do call
                    else:
                        d = self.trycall(x)
                        # process raw data
                        d = prep.ViewPrep([d])
                        # add to cache
                        print("... caching",callID)
                        cache.set(callID["hash"], d)
                        cacheIDs.append(callID)
                print("CALL done")
                return cacheIDs

    def trycall(self,x):
        print("... calling ", self.formatted[x])
        d = requests.get("https://api.sketchengine.eu/bonito/run.cgi/" + self.calltype, params={**self.formatted[x],**self.creds,**self.gparams})
        # check validity
        try:
            d = d.json()
            if "error" in d:
                print("ERROR-API:", d["error"])
            else:
                return d
        # show errors
        except:
            print("ERROR-other:", d)
        # wait
        print("... waiting", self.wait)
        time.sleep(self.wait)

    def unnest(self, df, explode, axis):
        """explode columns of lists
        https://stackoverflow.com/questions/53218931/how-to-unnest-explode-a-column-in-a-pandas-dataframe?noredirect=1"""
        if axis==1:
            df1 = pd.concat([df[x].explode() for x in explode], axis=1)
            return df1.join(df.drop(explode, 1), how='left')
        else :
            df1 = pd.concat([
                            pd.DataFrame(df[x].tolist(), index=df.index).add_prefix(x) for x in explode], axis=1)
            return df1.join(df.drop(explode, 1), how='left')

class view(Call):
    """
    subclass for view API usage
    """

    def __init__(
        self,
        params = {
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
        self.calltype = "view?"
        self.params = params
        self.clist = clist
        self.settings = settings
        self.formatted = self.format()
        self.labels = self.label()
        self.wait = self.setwait()
        self.results = []
        self.timestamp = datetime.now().isoformat()

    def dfview(self):
        dfs = pd.DataFrame()
        for x in range(len(self.results)):
            data = self.results[x]
            # make df
            df = pd.json_normalize(data["Lines"])
            # get refs (explode rename cols)
            df = self.unnest(df,["Refs"],axis=0)
            refs = data["request"]["refs"].split(",")
            df.rename(columns = {"Refs" + str(x): refs[x] for x in range(len(refs))}, inplace = True) 
            # get left, right
            df["Left"] = [x[0]["str"] if x else "" for x in df["Left"]]
            df["Right"] = [x[0]["str"] if x else "" for x in df["Right"]]
            # get kwic elements, md bold if labelled
            kwic = []
            for x in range(len(df)):
                row = "".join(["**" + x["str"] + "**" if x["class"] == "col0 coll coll" else x["str"] for x in df.iloc[0]["Kwic"]])
                kwic.append(row)
            df["Kwic"] = kwic
            # make conc
            df["kwic"] = df["Left"] + df["Kwic"] + df["Right"]
            # get corpname
            corpname = data["request"]["corpname"]
            df["corpname"] = corpname[corpname.rfind("/")+1:]
            df["concsize"] = data["concsize"]
            df["query"] = str(data["q"])
            df["fromp"] = data["fromp"]
            # TODO add label, cacheIDs, searchdate, version, other class vars
            # drop cols
            drops = ["toknum","hitlen","Tbl_refs","Left","Kwic","Right","Links","linegroup","linegroup_id"]
            df.drop(drops, axis=1, inplace=True)
            # reorder cols
            cols = list(df.columns)
            ordered = ["kwic","corpname","fromp","query","concsize"]
            ordered.extend([x for x in cols if x not in ordered]) # can use sorted([])
            df = df[ordered]
            # set dtypes manually
            df[["kwic"]] = df[["kwic"]].astype("string")
            df[["corpname", "query"]] = df[["corpname", "query"]].astype("category")
            # set dtypes automatically
            drops = ["kwic","corpname", "fromp", "query", "concsize"]
            categorical = [x for x in cols if x not in drops]
            df[categorical] = df[categorical].astype("category")
            # combine all results
            dfs = dfs.append(df)
        self.df = dfs

# clist = """
# "q": ''' "car" '''
# "q": ''' "water" '''
# # SINGLE
# "q": ''' "pie" '''
# "q": ''' "water" '''
# """

p = {'q': '"climate"','refs': 'doc,s', 'corpname': "preloaded/ecolexicon_en", 'viewmode': 'sen', 'pagesize': 100, 'fromp': 1}
s = {"qattr": "alemma,", "randomize": False}

# TODO dfview() add label, cacheIDs, searchdate, version, other class vars
# make workable with or without cache

c = view(p,s)
c.makecalls()
c.dfview()
c.df