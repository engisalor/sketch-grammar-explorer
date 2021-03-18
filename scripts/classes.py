import pathlib
import re
import json
import requests
import time
import subprocess
import hashlib
import pandas as pd

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

    def version(self):
        try:
            v = subprocess.check_output(["git", "describe",  "--always"]).decode("utf-8").strip()
            vdate = subprocess.check_output(["git", "show", "-s", "--format=%cd", "--date=short"]).decode("utf-8").strip()
            version = "{} / {}".format(vdate, v)
        except:
            version= "unknown"
        return version

    def format(self):
        # clean text
        ls = [x for x in self.clines.splitlines() if x]
        ls = [re.sub(' +', '',x) for x in ls]
        ls = ["".join(["{",x,"}"]) if not x.startswith("{") else x for x in ls]
        # set up each call
        dicts = [json.loads(x) for x in ls]
        dicts = [{**self.params, **dicts[x]} for x in range(len(dicts))]
       # repeat first q if call has none
        for x in range(len(dicts)):
            if "q" not in dicts[x]:
                dicts[x]["q"] = dicts[0]["q"]
        # get valid unique calls
        dicts = [x for x in self.unique(dicts) if x]
        # return with set q
        return [self.setq(x) for x in dicts]

    def unique(self,dicts):
        # make immutable
        strjson = [json.dumps(x, sort_keys=True) for x in dicts]
        # replace repeats with None starting from end
        for y in reversed(range(len(strjson))):
            if strjson.count(strjson[y]) > 1:
                strjson[y] = "None"
        # return to dicts
        return [json.loads(x) for x in strjson]

    def setq(self,call):
        if type(call["q"]) is str:
            r = ""
            if self.settings["randomize"] is True:
                r = "".join(["r", str(self.settings["pagesize"])])
                q = [self.settings["qattr"] + call["q"], r]
            else:
                q = [self.settings["qattr"] + call["q"]]
            call["q"] = q
        return call

    # def label(self):
    #     lines = self.clist.copy()
    #     # make calls comparable strings
    #     for x in range(len(lines)):
    #         if not lines[x].startswith("#"):
    #             if not lines[x].startswith("{"):
    #                 lines[x] = "".join(["{",lines[x],"}"])
    #             lines[x] = ast.literal_eval(lines[x])
    #             lines[x] = json.dumps(lines[x], sort_keys=True)
    #     lines = [x for x in self.unique(lines) if x]
    #     # add labels
    #     for x in range(len(lines)):
    #         # single labels
    #         if lines[x].startswith("#") and not lines[x].startswith("#",1):
    #             lines[x+1] = lines[x].strip("# ")
    #         # group labels
    #         if lines[x].startswith("###"):
    #             stop = [lines[x+1:].index(s) for s in lines[x+1:] if s.startswith("#")]
    #             # if a label exists after
    #             if len(stop) != 0:
    #                 for n in range(1,stop[0]+1):
    #                     lines[x+n] = lines[x].strip("# ")
    #             # if no labels after
    #             if len(stop) == 0:
    #                 for n in range(x+1,len(lines)):
    #                     lines[n] = lines[x].strip("# ")
    #         # if no label
    #         if lines[x].startswith("{"):
    #             lines[x] = None
    #     # drop old
    #     return [x for x in lines if x is None or not x.startswith("#")]

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
                    self.df = self.getdf(d)
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
                        d = self.getdf(d)
                        # add to cache
                        print("... caching")
                        cache.set(callID["hash"], d)
                        cacheIDs.append(callID)
                print("CALL done")
                return cacheIDs

    def trycall(self,x):
        print("... calling", self.formatted[x])
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
        https://stackoverflow.com/questions/53218931/how-to-unnest-explode-a-column-in-a-pandas.df?noredirect=1"""
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
            "label": "",
            "qattr": "alemma,",        
            "randomize": False},
        clines = ""):
        super().__init__()
        self.calltype = "view?"
        self.params = params
        self.clines = clines
        self.settings = settings
        self.formatted = self.format()
        # self.labels = self.label()
        self.wait = self.setwait()
        self.results = []
        self.timestamp = pd.Timestamp.now().isoformat()

    def getdf(self,data):
        """make a dataframe of view call results"""

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
        df["calltype"] = self.calltype
        df["version"] = self.version
        df["date"] = pd.Timestamp.fromisoformat(self.timestamp)
        # TODO add label, cacheIDs, version, other class vars
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
        drops = ["kwic","corpname", "fromp", "query", "concsize","date"]
        categorical = [x for x in cols if x not in drops]
        df[categorical] = df[categorical].astype("category")
        # combine all results
        return df

# p = {'refs': 'doc,s', 'corpname': "preloaded/ecolexicon_en", 'viewmode': 'sen', 'pagesize': 100, 'fromp': 1}
# s = {"qattr": "alemma,", "randomize": False}
# clines = '''
# {"corpname": "preloaded/ecolexicon_en", "fromp": 1, "pagesize": 100, "q": ["alemma,\\"salt\\""], "refs": "doc,s", "viewmode": "sen"}
# '''
# z = view(clines=clines)
# z.makecalls()
# z.df