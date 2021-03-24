import pathlib
import re
import json
import requests
import time
import subprocess
import hashlib
import pandas as pd
import ast

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
        # process text
        clines = re.sub('"""', "'''",self.clines)
        ls = [x for x in clines.splitlines() if x]
        ls = ["".join(["{",x,"}"]) if not x.startswith("{") else x for x in ls]
        # set up each call
        dicts = [ast.literal_eval(ls[x]) if "'''" in ls[x] else json.loads(ls[x]) for x in range(len(ls))]
        dicts = [{**self.params, **dicts[x]} for x in range(len(dicts))]
        # propagate queries and labels
        dicts = self.propagate(dicts)
        # remove extra spaces (exceptions: usesubcorp)
        dicts_clean = [dict() for x in range(len(dicts))]
        for x in range(len(dicts)):
            for key, item in dicts[x].items():
                if type(item) is str:
                    if key != "usesubcorp":
                        key_clean = re.sub(' +', '',key)
                        item_clean = re.sub(' +', '',item)
                        dicts_clean[x][key_clean] = item_clean
                    else:
                        dicts_clean[x][key] = item
                elif type(item) is list:
                    dicts_clean[x][key] = [re.sub(' +', '',x) if type(x) is str else x for x in item]
                else:
                    dicts_clean[x][key] = item
        # pop labels before finding unique calls   
        labels, trash = self.poplabels(dicts_clean)
        # get valid unique calls
        dicts_unique = [x for x in self.unique(dicts_clean)]
        # add labels to unique dicts
        dicts_unique_labelled = self.addlabels(dicts_unique,labels)
        # return with set q
        return [self.setq(x) for x in dicts_unique_labelled if type(x) is dict]

    def poplabels(self, dicts):
        temp = dicts.copy()
        labels = [x["l"] if "l" in x.keys() else "" for x in temp]
        for x in temp:
            if 'l' in x:
                del x['l']
        return labels, temp

    def addlabels(self, dicts,labels):
        temp = dicts.copy()
        for x in range(len(temp)):
            if type(temp[x]) is dict:
                temp[x]["l"] = labels[x]
        return temp

    def propagate(self,dicts,keys=["q","l"]):
        for key in keys:
            for x in range(len(dicts)):
                if key in dicts[x].keys():
                    stop = [dicts[x+1:].index(s) for s in dicts[x+1:] if key in s.keys()]
                    # if a key exists after
                    if len(stop) != 0:
                        for n in range(1,stop[0]+1):
                            dicts[x+n][key] = dicts[x][key]
                    # if no key after
                    if len(stop) == 0:
                        for n in range(x+1,len(dicts)):
                            dicts[n][key] = dicts[x][key]
        return dicts

    def unique(self,dicts):
        # make immutable
        strjson = [json.dumps(x, sort_keys=True) for x in dicts]
        # clear repeats in reverse order
        for y in reversed(range(len(strjson))):
            if 1 < strjson.count(strjson[y]):
                strjson[y] = "[]"
        # return to dicts
        return [json.loads(x) for x in strjson]

    def setq(self,call):
        if type(call["q"]) is str:
            if self.settings["randomize"]:
                if "pagesize" in call:
                    call["pagesize"] = ""
                q = [self.settings["qattr"] + call["q"], self.settings["randomize"]]
            else:
                q = [self.settings["qattr"] + call["q"]]
            call["q"] = q
        return call

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
            labels, calls = self.poplabels(self.formatted)
            # no cache
            if cache is None:
                for x in range(len(calls)):
                    jcall = json.dumps(calls[x], sort_keys=True)
                    hashed = hashlib.blake2s(jcall.encode()).hexdigest()
                    d = self.trycall(calls[x])
                    self.results.append(d)
                    self.df = self.df.append(self.getdf(d, jcall, hashed, labels[x]))
                    self.IDs.append(self.getID(d, jcall, hashed, labels[x]))
                    print("CALL done")
            # use cache
            else:
                # make cacheIDs if empty
                if cacheIDs is None:
                    cacheIDs = []
                for x in range(len(calls)):
                    # make callid
                    jcall = json.dumps(calls[x], sort_keys=True)
                    hashed = hashlib.blake2s(jcall.encode()).hexdigest()
                    # skip call if in cache
                    hashes = [cacheIDs[y]["hash"][0] for y in range(len(cacheIDs))]
                    if hashed in hashes:
                        print("... skipping", jcall)
                    # do call
                    else:
                        d = self.trycall(calls[x])
                        # process raw data
                        callID = self.getID(d, jcall, hashed, labels[x])
                        df = self.getdf(d, jcall, hashed, labels[x])
                        # add to cache
                        print("... caching")
                        cache.set(hashed, df)
                        cacheIDs.append(callID)
                print("CALL done")
                return cacheIDs

    def trycall(self,call):
        print("... calling", call)
        d = requests.get("https://api.sketchengine.eu/bonito/run.cgi/" + self.calltype, params={**call,**self.creds,**self.gparams})
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
            "corpname": "preloaded/ecolexicon_en",
            # "usesubcorp": "Language variant - American English",
            "pagesize": 20,
            "fromp": "1",
            "refs": "doc,s",
            "viewmode": "sen"},
        settings = {
            "label": "",
            "qattr": "alemma,",        
            "randomize": ""}, # '', 'rN' where N is sample size, or 'rN%' where n is a percent value
        clines = ""):
        super().__init__()
        self.calltype = "view?"
        self.params = params
        self.clines = clines
        self.settings = settings
        self.formatted = self.format()
        self.df = pd.DataFrame()
        self.IDs = []
        self.wait = self.setwait()
        self.results = []
        self.timestamp = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")

    def getID(self,data, jcall, hashed, label):
        """make dict of view callID"""

        callID = {
            "label": [label], 
            "type": [self.calltype], 
            "call": [jcall],
            "date": [self.timestamp],
            "fullsize": [data["fullsize"]],
            "length": [len(data["Lines"])],
            "hash": [hashed],
            }
        return callID

    def getdf(self,data, jcall, hashed, label):
        """make dataframe of view call results"""
        df = pd.json_normalize(data["Lines"])
        # get refs (explode, rename cols)
        if "refs" in self.params:
            if self.params["refs"]:
                df = self.unnest(df,["Refs"],axis=0)        
                refs = data["request"]["refs"].split(",")
                df.rename(columns = {"Refs" + str(x): refs[x] for x in range(len(refs))}, inplace = True)
            else:
                df.drop("Refs", axis=1, inplace=True)
        else:
            df.drop("Refs", axis=1, inplace=True)
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
        corpname = data["request"]["corpname"]
        df["corpname"] = corpname[corpname.rfind("/")+1:]
        df["label"] = label
        if "fromp" in data:
            df["fromp"] = data["fromp"]
        else:
            df["fromp"] = 1
        df["hit"] = df["fromp"].astype(str) + "." + df.index.astype(str)
        # drop cols
        drops = ["fromp", "toknum","hitlen","Tbl_refs","Left","Kwic","Right","Links","linegroup","linegroup_id"]
        df.drop(drops, axis=1, inplace=True)
        # reorder cols
        cols = list(df.columns)
        ordered = ["label", "hit", "kwic", "corpname"]
        ordered.extend([x for x in cols if x not in ordered]) # can use sorted([])
        df = df[ordered]
        # set dtypes manually
        df[["kwic"]] = df[["kwic"]].astype("string")
        # set dtypes automatically
        drops = ["hit", "kwic"]
        categorical = [x for x in cols if x not in drops]
        df[categorical] = df[categorical].astype("category")
        return df

# TODO "size" is ambiguous for id table
# TODO what about storing raw data in cache and converting to pandas on the fly?

# s = {"qattr": "alemma,", "randomize": ""}
# p = {"usesubcorp": "Language variant - American English",'refs': 'doc,s', 'corpname': "preloaded/ecolexicon_en", 'viewmode': 'sen', 'pagesize': 20, 'fromp': 1}
# clines = """
# "q": "\\"water\\"", "usesubcorp": "Language variant - American English"
# """
# z = view(clines=clines)
# z.makecalls()