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
    """Parent class for all API call types

    Defines the basic call structure
    Supplies the methods needed for building and making any type of call
    """

    def __init__(self, global_parameters={"asyn": "0", "format": "json"}):
        self.global_parameters = global_parameters
        self.credentials = self.set_creds()
        self.version = self.set_vers()

    def set_creds(self, filepath=".auth_api.txt"):
        """Get SkE API credentials from file"""

        with open(pathlib.Path(filepath)) as f:
            return dict(line.rstrip().split(":") for line in f)

    def set_vers(self):
        """Get the latest commit and modified date"""

        try:
            commit = (
                subprocess.check_output(["git", "describe", "--always"])
                .decode("utf-8")
                .strip()
            )
            date = (
                subprocess.check_output(
                    ["git", "show", "-s", "--format=%cd", "--date=short"]
                )
                .decode("utf-8")
                .strip()
            )
            version = "{} / {}".format(date, commit)
        except:
            version = "unknown"

        return version

    def format_text(self):
        """Extract and format calls from text input"""

        # Preprocess text
        calls_str = re.sub('"""', "'''", self.calls_str)
        calls_list = [line for line in calls_str.splitlines() if line]
        calls_list = [
            "".join(["{", line, "}"]) if not line.startswith("{") else line
            for line in calls_list
        ]

        # Parse list items
        calls_dicts = [
            ast.literal_eval(calls_list[x])
            if "'''" in calls_list[x]
            else json.loads(calls_list[x])
            for x in range(len(calls_list))
        ]

        # Remove spaces
        needs_spaces = ["usesubcorp"]

        for call in calls_dicts:
            call = {re.sub(" +", "", k): v for k, v in call.items()}
            call = {
                k: re.sub(" +", "", v)
                for k, v in call.items()
                if v not in needs_spaces and type(v) is str
            }

        # Propagate unique parameters
        calls_draft = self.propagate(calls_dicts)

        # Manage labels, repeats
        labels, _ = self.pop_labels(calls_draft)
        calls_unique = [x for x in self.unique(calls_draft)]
        calls_unique_labelled = self.add_labels(calls_unique, labels)

        return [item for item in calls_unique_labelled if type(item) is dict]

    def pop_labels(self, calls):
        """Extract labels from a list of calls"""

        temp = calls.copy()
        labels = [call["l"] if "l" in call.keys() else "" for call in temp]

        for x in temp:
            if "l" in x:
                del x["l"]

        return labels, temp

    def add_labels(self, calls, labels):
        """Reinsert labels for a list of calls"""

        temp = calls.copy()

        for x in range(len(temp)):
            if type(temp[x]) is dict:
                temp[x]["l"] = labels[x]

        return temp

    def propagate(self, calls):
        """Reuse API parameters unless defined explicitly"""

        for key in calls[0].keys():
            for x in range(len(calls)):
                if key in calls[x].keys():
                    stop = [
                        calls[x + 1 :].index(s)
                        for s in calls[x + 1 :]
                        if key in s.keys()
                    ]

                    # If a key exists after
                    if len(stop) != 0:
                        for n in range(1, stop[0] + 1):
                            calls[x + n][key] = calls[x][key]

                    # If no key after
                    if len(stop) == 0:
                        for n in range(x + 1, len(calls)):
                            calls[n][key] = calls[x][key]
        return calls

    def unique(self, calls):
        """Replace repeated calls with an empty list"""

        calls_str = [json.dumps(x, sort_keys=True) for x in calls]

        # Clear repeats in reverse order
        for y in reversed(range(len(calls_str))):
            if 1 < calls_str.count(calls_str[y]):
                calls_str[y] = "[]"

        return [json.loads(call) for call in calls_str]

    def setwait(self):
        """Set wait time for SkE API usage"""

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

    def dry_run(self, cache=None):
        """Print call details"""

        print("DRY RUN")
        print("... call type:", self.call_type)
        print("... timestamp:", self.timestamp)
        print("... version:", self.version)
        print("... calls:", len(self.formatted))
        print("... wait:", self.wait)
        print(
            "... credentials:",
            self.credentials["username"],
            "/",
            self.credentials["api_key"][0:5] + "...",
        )
        print("... cache:", cache)
        print("... global parameters:", self.global_parameters)

        for x in range(len(self.formatted)):
            print("... call{}:".format(str(x)), self.formatted[x])

    def make_calls(self, cache=None, cache_IDs=None, dry_run=False):
        """Make API call(s) and store results in instance or cache"""

        if dry_run is True:
            self.dry_run(cache)
        else:
            print("CALLS start")
            labels, calls = self.pop_labels(self.formatted)

            for x in range(len(calls)):
                call_str = json.dumps(calls[x], sort_keys=True)
                call_hash = hashlib.blake2s(call_str.encode()).hexdigest()

                # Skip existing call
                hashes = []

                if cache_IDs is not None:
                    hashes = [cache_IDs[y]["hash"][0] for y in range(len(cache_IDs))]
                if call_hash in hashes:
                    print("... skipping", call_str)

                # Make call and append results
                else:
                    result_json = self.try_call(calls[x])
                    self.results.append(result_json)
                    self.df = self.df.append(
                        self.getdf(result_json, call_str, call_hash, labels[x])
                    )
                    self.set_dtypes()
                    self.IDs.append(
                        self.get_ID(result_json, call_str, call_hash, labels[x])
                    )

            # Cache results
            if cache is not None:
                dfs_cached = cache.get("results_df")
                if dfs_cached is None:
                    dfs_cached = pd.DataFrame()
                dfs_cached = dfs_cached.append(self.df)
                cache.set("results_df", dfs_cached)

            print("CALLS done")

    def set_dtypes(self):
        """Set best datatype for each column in self.df"""

        for col in self.df.columns:
            if len(self.df[col].unique()) / len(self.df[col]) < 0.50:
                self.df[col] = self.df[col].astype("category")
            else:
                pass

    def try_call(self, call):
        """Try making a single API call or show errors"""

        print("... calling", call)
        result = requests.get(
            "https://api.sketchengine.eu/bonito/run.cgi/" + self.call_type,
            params={**call, **self.credentials, **self.global_parameters},
        )

        # Check validity
        try:
            result_json = result.json()
            if "error" in result_json:
                print("ERROR-API:", result_json["error"])
            else:
                return result_json

        # Show errors
        except:
            print("ERROR-other:", result_json)

        # Wait
        print("... waiting", self.wait)
        time.sleep(self.wait)

    def unnest(self, df, explode, axis):
        """Explode columns containing lists

        Source https://stackoverflow.com/questions/53218931/"""

        if axis == 1:
            temp = pd.concat([df[x].explode() for x in explode], axis=1)
            return temp.join(df.drop(explode, 1), how="left")
        else:
            temp = pd.concat(
                [
                    pd.DataFrame(df[x].tolist(), index=df.index).add_prefix(x)
                    for x in explode
                ],
                axis=1,
            )
            return temp.join(df.drop(explode, 1), how="left")


class view(Call):
    """Subclass with variables and methods for view API calls"""

    def __init__(self, calls_str):
        super().__init__()
        self.call_type = "view?"
        self.calls_str = calls_str
        self.formatted = self.format_text()
        self.wait = self.setwait()
        self.timestamp = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        self.results = []
        self.IDs = []
        self.df = pd.DataFrame()

    def get_ID(self, result_json, call_str, call_hash, label):
        """Make a dict with view call details"""

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

    def getdf(self, result_json, call_str, call_hash, label):
        """Make a dataframe of view call results"""

        df = pd.json_normalize(result_json["Lines"])

        # Get left, right context
        df["Left"] = [x[0]["str"] if x else "" for x in df["Left"]]
        df["Right"] = [x[0]["str"] if x else "" for x in df["Right"]]

        # Get kwic elements & add .md bold format if defined
        kwics = []

        for x in range(len(df)):
            row = "".join(
                [
                    "**" + x["str"] + "**"
                    if x["class"] == "col0 coll coll"
                    else x["str"]
                    for x in df.iloc[0]["Kwic"]
                ]
            )
            kwics.append(row)

        df["Kwic"] = kwics

        # Make full concordance
        df["kwic"] = df["Left"] + df["Kwic"] + df["Right"]
        corpname = result_json["request"]["corpname"]

        # Make other columns
        df["corpname"] = corpname[corpname.rfind("/") + 1 :]

        if "usesubcorp" in result_json["request"]:
            df["subcorp"] = result_json["request"]["usesubcorp"]

        df["label"] = label

        if "fromp" in result_json:
            df["fromp"] = result_json["fromp"]
        else:
            df["fromp"] = 1

        df["hit"] = df.index
        df["hash"] = call_hash

        # Drop columns
        drops = [
            "toknum",
            "hitlen",
            "Tbl_refs",
            "Left",
            "Kwic",
            "Right",
            "Links",
            "linegroup",
            "linegroup_id",
        ]
        df.drop(drops, axis=1, inplace=True)

        # Un-nest columns containing lists
        explodes = [col for col in df.columns if type(df.iloc[0][col]) is list]
        df = self.unnest(df, explodes, axis=0)

        # Reorder cols
        cols = list(df.columns)
        ordered = ["label", "fromp", "hit", "kwic", "corpname"]

        if "usesubcorp" in result_json["request"]:
            ordered.append("subcorp")

        ordered.extend([x for x in cols if x not in ordered])  # can use sorted([])
        df = df[ordered]

        return df


# TODO "size" is ambiguous for id table
# TODO enable changing call types, w/ hiding/generating components
# TODO add dry_run w/ log in app
# TODO load data from file

# calls_str = """
# "q": ["alemma,\\"ice\\""], "refs": "doc,s", "corpname": "preloaded/ecolexicon_en", "viewmode": "sen", "pagesize": 10, "fromp": 1
# """
# z = view(calls_str=calls_str)
# z.make_calls(dry_run=True)
