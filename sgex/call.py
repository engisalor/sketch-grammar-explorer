import pathlib
import json
import requests
import time
import hashlib
import pandas as pd
import yaml
import sqlite3 as sql

import sgex


class Call:
    """Executes Sketch Engine API calls, saves data to sqlite database.

    Options

    `input` a dictionary or a path to a YAML/JSON file containing API calls

    `db` define a database to use (`"sgex.db"`)

    `dry_run` make a `Call` object that can be inspected before executing requests (`False`)
      - `object` prints a job summary
      - `object.calls` accesses all call details

    `skip` skip calls when identical calls already exist in the destination folder (`True`)
      - based on a hash of unique call parameters

    `clear` remove existing data before running current calls (`False`)

    `timestamp` include a timestamp (`True`)

    `keep` only save desired json items (`None` - saves everything)
      - a str (if one item), otherwise a list/dict

    `server` specify what server to call (`"https://api.sketchengine.eu/bonito/run.cgi"`)
      - must omit trailing forward slashes

    `wait` enable waiting between calls (`True`)

    `asyn` retrieve rough calculations, `"0"` (default) or `"1"`"""


    def _credentials(self):
        """Gets SkE API credentials from keyring/file.

        - default file is "config.yml"
        - ".config.yml" can be used as well (has priority over default file)
        """

        credentials = None
        path = pathlib.Path("")
        files = list(path.glob("*config.yml"))
        hidden_config = ".config.yml" in [x.name for x in files]

        if hidden_config:
            file = path / ".config.yml"
        else:
            file = path / "config.yml"

        # Open file
        with open(file, "r") as stream:
            credentials = yaml.safe_load(stream)

        credentials = {
            k.strip(): v.strip() for k, v in credentials[self.server].items()
        }

        # Try keyring
        if not credentials["api_key"]:
            import keyring

            credentials["api_key"] = keyring.get_password(
                self.server, credentials["username"]
            )
        if not credentials["api_key"] or not credentials["username"]:
            raise ValueError("No API key/username found")

        return credentials

    def _hashes_add(self):
        """Adds hashes to calls."""

        for i in self.calls.values():
            call_json = json.dumps(i["call"], sort_keys=True)
            i["hash"] = hashlib.blake2b(call_json.encode()).hexdigest()[0:32]

    def _hashes_compare(self):
        """Compares hashes with existing data, sets skip values."""

        # No skip by default
        for x in self.calls.values():
            x["skip"] = False

        # Get existing calls
        for x in self.calls.values():
            # Get existing hashes
            self.c.execute("select hash from calls")
            output = self.c.fetchall()
            hashes = set([x[0] for x in output])

        # Compare hashes and set skip values
        for x in self.calls.values():
            if x["hash"] in hashes and self.skip:
                x["skip"] = True

    def _reuse_parameters(self):
        """Reuses parameters unless defined explicitly.
        
        Parameters are reused for sequential calls of the same type. If a call
        type is specified, nothing is reused. Otherwise, when a parameter changes,
        it will be reused until redefined again in a later call.

        If parameters are part of a dictionary, individual key:values are reused.
        Otherwise, the item is replaced flatly."""

        ls = [(k, v) for k, v in self.calls.items()]
        for x in range(len(ls)):
            if x == 0 or "type" in ls[x][1]:
                pass
            else:
                id = ls[x][0]

                # Flat copy previous call
                previous = {**ls[x - 1][1]}
                current = {**ls[x][1]}
                self.calls[id] = {**previous, **current}

                # Replace individual dictionary values
                for k,v in ls[x][1].items():
                    if isinstance(v,dict):
                        self.calls[id][k] = {**{**ls[x - 1][1][k]}, **{**ls[x][1][k]}}

        """Sets wait time for SkE API usage."""

        n = len(self.calls)
        if n == 1 or not self.wait_enabled:
            wait = 0
        elif 2 <= n < 100:
            wait = 2
        elif 100 <= n < 900:
            wait = 5
        elif 900 <= n:
            wait = 45

        self.wait = wait

    def _do_call(self, v, k, credentials):
        """Runs or skip an api call."""

        self.response = None
        if not v["skip"]:
            parameters = {
                **credentials,
                **self.global_parameters,
                **v["call"],
            }
            
            t0 = time.perf_counter()
            self.response = requests.get(self.url_base, params=parameters)
            t1 = time.perf_counter()
    
            # Error detection
            if not self.response:
                print(f"... bad response: {self.response}")
            else:
                self.error = None
                if "error" in self.response.json():
                    self.error = self.response.json()["error"]
                    print(f"... {t1 - t0:0.2f} secs:", k, "error:", self.error)
                else:
                    print(f"... {t1 - t0:0.2f} secs:", k)
    
    def _post_call(self, v, k):
        """Saves API response data to sqlite database."""

        # Keep only desired data
        # FIXME works for flat dict: what about supporting nested dicts?
        if self.keeps:
            kept = {k:v for k,v in self.response.json().items() if k in self.keeps}
            data = json.dumps(kept)
        else:
            data = json.dumps(self.response.json())

        # Add metadata
        meta = None
        if "meta" in v.keys():
            if isinstance(v["meta"], (dict, list, tuple)):
                meta = json.dumps(v["meta"], sort_keys=True)
            else:
                meta = v["meta"]

        # Write to db
        self.c.execute(
            "INSERT OR REPLACE INTO calls VALUES (?,?,?,?,?,?,?,?,?)",
            (
                self.input,
                self.call_type[:-1],
                k,
                v["hash"],
                self.timestamp,
                json.dumps(v["call"], sort_keys=True),
                meta,
                self.error,
                data,
            ),
            )
        self.conn.commit()

        # Wait
        time.sleep(self.wait)

    def _make_calls(self, credentials):
        """Manages the API call process (do_call & post_call)."""

        if self.dry_run:
            pass
        else:
            if self.clear:
                print("... clearing")
                self.c.execute("DROP TABLE calls")
                self._make_table()
                self.conn.commit()
                for x in self.calls.values():
                    x["skip"] = False

            for k, v in self.calls.items():
                self._do_call(v, k, credentials)
                if self.response:
                    self._post_call(v, k)

    def _make_table(self):
        self.c.execute(
            """CREATE TABLE IF NOT EXISTS calls (
            input,
            type text,
            id text,
            hash text PRIMARY KEY,
            timestamp text,
            call text,
            meta text,
            error text,
            response text) WITHOUT ROWID"""
        )
        self.c.execute("pragma journal_mode = WAL")
        self.c.execute("pragma synchronous = normal")

    def __repr__(self) -> str:
        """Prints job details."""

        dt = {
            "timestamp  ": self.timestamp,
            "input      ": self.input,
            "db         ": self.db,
            "server     ": self.server,
            "keep       ": self.keeps,
            "calls      ": len(self.calls),
            "wait       ": self.wait,
            "skip       ": self.skip,
            "clear      ": self.clear,
        }

        s = [" ".join([k, str(v)]) for k, v in dt.items()]
        s = "\n".join(s)

        return s

    def __init__(
        self,
        input,
        db="sgex.db",
        dry_run=False,
        skip=True,
        clear=False,
        timestamp=True,
        keep=None,
        server="https://api.sketchengine.eu/bonito/run.cgi",
        wait=True,
        asyn="0",
    ):
        t0 = time.perf_counter()

        # Settings
        self.dry_run = dry_run
        self.skip = skip
        self.clear = clear
        self.global_parameters = {"asyn": asyn, "format": "json"}
        self.server = server.strip("/")
        self.wait_enabled = wait
        self.input = "dict"
        self.timestamp = None
        self.keeps = keep
        self.db = "".join(["data/", db])

        if isinstance(keep, str):
            self.keep = [keep]
        if timestamp:
            self.timestamp = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(input, str):
            self.input = pathlib.Path(input).name

        # Database
        pathlib.Path.mkdir(pathlib.Path("data"),exist_ok=True)
        self.conn = sql.connect(self.db)
        self.c = self.conn.cursor()
        self._make_table()

        # Execute
        self.calls = sgex.Parse(input).calls

        if not self.calls:
            pass
        else:
            self.call_type = "".join([self.calls["type"], "?"])
            del self.calls["type"]
            self.url_base = "/".join([self.server, self.call_type])

            credentials = self._credentials()
            self._wait()
            self._reuse_parameters()
            self._hashes_add()
            self._hashes_compare()
            self._make_calls(credentials)

        # Close
        self.c.close()
        self.conn.close()

        t1 = time.perf_counter()
        print(f"... {t1 - t0:0.2f} secs total")