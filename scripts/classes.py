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
 
    def __init__(self,global_parameters={"asyn":"0", "format":"json"}):
        self.global_parameters = global_parameters
        self.credentials = self.set_creds()
        self.version = self.set_vers()

    def set_creds(self, filepath=".auth_api.txt"):
        with open(pathlib.Path(filepath)) as f:
            return dict(line.rstrip().split(":") for line in f)

    def set_vers(self):
        try:
            commit = subprocess.check_output(["git", "describe",  "--always"]).decode("utf-8").strip()
            date = subprocess.check_output(["git", "show", "-s", "--format=%cd", "--date=short"]).decode("utf-8").strip()
            version = "{} / {}".format(date, commit)
        except:
            version= "unknown"
        return version

    def format_text(self):
        # preprocess text
        calls_str = re.sub('"""', "'''",self.calls_str)
        calls_list = [line for line in calls_str.splitlines() if line]
        calls_list = ["".join(["{",line,"}"]) if not line.startswith("{") else line for line in calls_list]
        # parse list items 
        calls_dicts = [ast.literal_eval(calls_list[x]) if "'''" in calls_list[x] else json.loads(calls_list[x]) for x in range(len(calls_list))]
        # propagate unique parameters
        calls_draft = Call.propagate(None,calls_dicts)
        # remove extra spaces (exceptions: usesubcorp)
        calls_clean = [dict() for dt in range(len(calls_draft))]
        for x in range(len(calls_draft)):
            for key, item in calls_draft[x].items():
                if type(item) is str:
                    if key != "usesubcorp":
                        key_clean = re.sub(' +', '',key)
                        item_clean = re.sub(' +', '',item)
                        calls_clean[x][key_clean] = item_clean
                    else:
                        calls_clean[x][key] = item
                elif type(item) is list:
                    calls_clean[x][key] = [re.sub(' +', '',string) if type(string) is str else string for string in item]
                else:
                    calls_clean[x][key] = item
        # pop labels before finding unique calls   
        labels, _ = self.pop_labels(calls_clean)
        # get valid unique calls
        calls_unique = [x for x in self.unique(calls_clean)]
        # add labels to unique calls
        calls_unique_labelled = self.add_labels(calls_unique,labels)

        return [dt for dt in calls_unique_labelled if type(dt) is dict]

    def pop_labels(self, calls):
        temp = calls.copy()
        labels = [call["l"] if "l" in call.keys() else "" for call in temp]
        for x in temp:
            if 'l' in x:
                del x['l']
        return labels, temp

    def add_labels(self, calls,labels):
        temp = calls.copy()
        for x in range(len(temp)):
            if type(temp[x]) is dict:
                temp[x]["l"] = labels[x]
        return temp

    def propagate(self,calls):
        for key in calls[0].keys():
            for x in range(len(calls)):
                if key in calls[x].keys():
                    stop = [calls[x+1:].index(s) for s in calls[x+1:] if key in s.keys()]
                    # if a key exists after
                    if len(stop) != 0:
                        for n in range(1,stop[0]+1):
                            calls[x+n][key] = calls[x][key]
                    # if no key after
                    if len(stop) == 0:
                        for n in range(x+1,len(calls)):
                            calls[n][key] = calls[x][key]
        return calls

    def unique(self,calls):
        # make immutable
        calls_str = [json.dumps(x, sort_keys=True) for x in calls]
        # clear repeats in reverse order
        for y in reversed(range(len(calls_str))):
            if 1 < calls_str.count(calls_str[y]):
                calls_str[y] = "[]"
        # return to calls
        return [json.loads(call) for call in calls_str]

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

    def dry_run(self,cache=None):
        print("dry_run")
        print("... call type:", self.call_type)
        print("... timestamp:",self.timestamp)
        print("... version:",self.version)
        print("... calls:", len(self.formatted))
        print("... wait:", self.wait)
        print("... credentials:",self.credentials["username"],"/", self.credentials["api_key"][0:5] + "...")
        print("... cache:", cache)
        print("... global parameters:", self.global_parameters)
        for x in range(len(self.formatted)):
            print("... call{}:".format(str(x)), self.formatted[x])

    def make_calls(self,cache=None,cache_IDs=None,dry_run=False):
        if dry_run is True:
            self.dry_run(cache)
        else:
            print("CALLS start")
            labels, calls = self.pop_labels(self.formatted)

            for x in range(len(calls)):
                call_str = json.dumps(calls[x], sort_keys=True)
                call_hash = hashlib.blake2s(call_str.encode()).hexdigest()
                
                # skip existing call
                hashes = []
                if cache_IDs is not None:
                    hashes = [cache_IDs[y]["hash"][0] for y in range(len(cache_IDs))]
                if call_hash in hashes:
                    print("... skipping", call_str)

                # make call and append results
                else:
                    result_json = self.trycall(calls[x])
                    self.results.append(result_json)
                    self.df = self.df.append(self.getdf(result_json, call_str, call_hash, labels[x]))
                    self.set_dtypes()
                    self.IDs.append(self.getID(result_json, call_str, call_hash, labels[x]))

            # cache results for app
            if cache is not None:
                dfs_cached = cache.get("results_df")
                if dfs_cached is None:
                    dfs_cached = pd.DataFrame()
                dfs_cached = dfs_cached.append(self.df)
                cache.set("results_df", dfs_cached)

            print("CALLS done")

    def set_dtypes(self):
        """set best datatype for each column in self.df"""

        str_cols = ["kwic"]
        for col in self.df.columns:
            if col in str_cols:
                self.df[col] = self.df[col].astype(str)
            elif len(self.df[col].unique()) / len(self.df[col]) < 0.50:
                self.df[col] = self.df[col].astype("category")
            else:
                pass

    def trycall(self,call):
        print("... calling", call)
        result = requests.get("https://api.sketchengine.eu/bonito/run.cgi/" + self.call_type, params={**call,**self.credentials,**self.global_parameters})
        # check validity
        try:
            result_json = result.json()
            if "error" in result_json:
                print("ERROR-API:", result_json["error"])
            else:
                return result_json
        # show errors
        except:
            print("ERROR-other:", result_json)
        # wait
        print("... waiting", self.wait)
        time.sleep(self.wait)

    def unnest(self, df, explode, axis):
        """explode columns of lists
        https://stackoverflow.com/questions/53218931/how-to-unnest-explode-a-column-in-a-pandas.df?noredirect=1"""
        if axis==1:
            temp = pd.concat([df[x].explode() for x in explode], axis=1)
            return temp.join(df.drop(explode, 1), how='left')
        else :
            temp = pd.concat([
                            pd.DataFrame(df[x].tolist(), index=df.index).add_prefix(x) for x in explode], axis=1)
            return temp.join(df.drop(explode, 1), how='left')

class view(Call):
    """
    subclass for view API usage
    """

    def __init__(self, calls_str):
        super().__init__()
        self.call_type = "view?"
        self.calls_str = calls_str
        self.formatted = self.format_text()
        self.df = pd.DataFrame()
        self.IDs = []
        self.wait = self.setwait()
        self.results = []
        self.timestamp = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")

    def getID(self,result_json, call_str, call_hash, label):
        """make dict of view callID"""

        callID = {
            "label": [label], 
            "type": [self.call_type], 
            "call": [call_str],
            "date": [self.timestamp],
            "fullsize": [result_json["fullsize"]],
            "length": [len(result_json["Lines"])],
            "hash": [call_hash],
            }
        return callID

    def getdf(self,result_json, call_str, call_hash, label):
        """make dataframe of view call results"""
        df = pd.json_normalize(result_json["Lines"])
        # get refs (explode, rename cols)
        call_dt = json.loads(call_str)
        if "refs" in call_dt:
            if call_dt["refs"]:
                df = self.unnest(df,["Refs"],axis=0)        
                refs = result_json["request"]["refs"].split(",")
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
        corpname = result_json["request"]["corpname"]
        df["corpname"] = corpname[corpname.rfind("/")+1:]
        if "usesubcorp" in result_json["request"]:
            df["subcorp"] = result_json["request"]["usesubcorp"]
        df["label"] = label
        if "fromp" in result_json:
            df["fromp"] = result_json["fromp"]
        else:
            df["fromp"] = 1
        df["hit"] = df.index
        df["hash"] = call_hash
        # drop cols
        drops = ["toknum","hitlen","Tbl_refs","Left","Kwic","Right","Links","linegroup","linegroup_id"]
        df.drop(drops, axis=1, inplace=True)
        # reorder cols
        cols = list(df.columns)
        ordered = ["label", "fromp","hit", "kwic", "corpname"]
        if "usesubcorp" in result_json["request"]:
            ordered.append("subcorp")
        ordered.extend([x for x in cols if x not in ordered]) # can use sorted([])
        df = df[ordered]
        # strip non digits
        strips = ["doc", "s"]
        for col in df.columns:
            if col in strips:
                df[col] = [int(re.sub(r'[^\d]+','',row)) for row in df[col]]
        return df

# TODO test for best setdtype memory usage
# TODO what else should be progagated: pagesize, etc?
# TODO "size" is ambiguous for id table
# TODO what about storing raw data in cache and converting to pandas on the fly?
# TODO enable changing call types, w/ hiding/generating components
# TODO add dry_run w/ log in app
# TODO load data from file

# calls_str = """
# "q": ["alemma,\\"space\\""], "refs": "doc,s", "corpname": "preloaded/ecolexicon_en", "viewmode": "sen", "pagesize": 10, "fromp": 1
# """
# z = view(calls_str=calls_str)
# z.make_calls()