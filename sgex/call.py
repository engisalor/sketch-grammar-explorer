import pathlib
import json
import requests
import time
import hashlib
import pandas as pd
import yaml
import sqlite3 as sql
from concurrent.futures import ThreadPoolExecutor

import sgex


class Call:
    """Executes Sketch Engine API calls & saves data to sqlite database.

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

    `server` specify what server to call (`"https://api.sketchengine.eu/bonito/run.cgi"`)
      - must omit trailing forward slashes

    `wait` enable waiting between calls (`True`)

    `asyn` retrieve rough calculations, `"0"` (default) or `"1"`

    `threads` number of threads when running calls asynchronously (18)
      - asynchronous calling is activated when using a local server & `wait=False`"""

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
        
        Parameters are reused for sequential calls of the same type. If `type`
        is specified, nothing is reused. Otherwise, when a parameter changes,
        it will be reused until redefined again in a later call.

        If parameters are part of a dictionary, individual key:values are reused.
        Otherwise, the item is replaced flatly."""

        def _propagate(ls, k):
            for x in range(1, len(ls)):
                current = ls[x][1]
                id = ls[x][0]
                previous = ls[x - 1][1] 
                if k in current and k != "type":
                    if isinstance(current[k], dict):
                        p_dt = {**previous[k]}
                        c_dt = {**current[k]}
                        self.calls[id][k] = {**p_dt, **c_dt}
                    else:
                        self.calls[id][k] = current[k]
                else:
                    if k in previous:
                        self.calls[id][k] = previous[k]

        ls = [(k, v) for k, v in self.calls.items()]
        [_propagate(ls, k) for k in ["type", "meta", "keep", "call"]]

    def _set_wait(self):
        """Sets wait time for SkE API usage."""

        # TODO allow user to define wait values
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

    def _make_manifest(self, credentials):
        """Makes a call manifest with ids, params & request urls."""

        req = requests.models.PreparedRequest()
        manifest = []

        for k, v in self.calls.items():
            if not v["skip"]:
                parameters = {
                    **credentials,
                    **self.global_parameters,
                    **v["call"],
                }

                call_type = "".join([v["type"], "?"])
                url_base = "/".join([self.server, call_type])
                req.prepare_url(url_base, parameters)
                manifest.append({"id": k, "params": v, "url": req.url})

        return manifest

    def _make_calls(self, manifest):
        """Runs calls in manifest sequentially."""

        for manifest_item in manifest:
            # Run call
            self.t0 = time.perf_counter()
            response = requests.get(manifest_item["url"])
            self.t1 = time.perf_counter()
            self._print_progress(response, manifest_item)

            # Process packet
            packet = {"item": manifest_item, "response": response}
            self._post_call(packet)

            # Wait
            time.sleep(self.wait)

    def _make_local_calls(self, manifest):
        """Runs calls in manifest asynchronously.
        
        Enabled when using a local server & `wait=False`."""

        THREAD_POOL = self.threads
        session = requests.Session()
        session.mount(
            'https://',
            requests.adapters.HTTPAdapter(pool_maxsize=THREAD_POOL,
                                        # max_retries=3,
                                        pool_block=True)
        )

        def get(manifest_item):
            self.t0 = time.perf_counter()
            response = session.get(manifest_item["url"])
            self.t1 = time.perf_counter()
            self._print_progress(response, manifest_item)
            return {"item": manifest_item, "response": response}

        with ThreadPoolExecutor(max_workers=THREAD_POOL) as executor:
            for packet in list(executor.map(get, manifest)):
                # Process packets
                self._post_call(packet)

    def _post_call(self, packet):
        """Processes and saves call data."""

        if not packet["response"]:
            print("... bad response:", packet["response"])
        else:
            error = None
            if "error" in packet["response"].json():
                error = packet["response"].json()["error"]

            # Keep only desired data
            # FIXME works for flat dict: what about supporting nested dicts?
            if "keep" in packet["item"]["params"]:
                keep = packet["item"]["params"]["keep"]
                if isinstance(keep, str):
                    keeps = [keep]
                kept = {k:v for k,v in packet["response"].json().items() if k in keeps}
                data = json.dumps(kept)
            else:
                data = json.dumps(packet["response"].json())

            # Add metadata
            meta = None
            if "meta" in packet["item"]["params"].keys():
                if isinstance(packet["item"]["params"]["meta"], (dict, list, tuple)):
                    meta = json.dumps(packet["item"]["params"]["meta"], sort_keys=True)
                else:
                    meta = packet["item"]["params"]["meta"]

            # Write to db
            self.c.execute(
                "INSERT OR REPLACE INTO calls VALUES (?,?,?,?,?,?,?,?,?)",
                (
                    self.input,
                    packet["item"]["params"]["type"][:-1],
                    packet["item"]["id"],
                    packet["item"]["params"]["hash"],
                    self.timestamp,
                    json.dumps(packet["item"]["params"]["call"], sort_keys=True),
                    meta,
                    error,
                    data,
                ),
                )

            # Finish task
            self.conn.commit()
            print(f"... {self.t1 - self.t0:0.2f}", packet["item"]["id"], end=" ")
            if error:
                print(error)
            else:
    def _print_progress(self,response, manifest_item):
        if self.progress:
            error = ""
            if self.db in self.db_extensions:
                error = ""
                if "error" in response.json():
                    error = response.json()["error"]
            print(f"{self.t1 - self.t0:0.2f}", manifest_item["id"], error)

    def _pre_calls(self):
        if self.dry_run:
            for x in self.calls.values():
                x["skip"] = True
        else:
            if self.clear:
                print("... clearing", self.db)
                self.c.execute("DROP TABLE calls")
                self._make_table()
                self.conn.commit()
                for x in self.calls.values():
                    x["skip"] = False

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
        server="https://api.sketchengine.eu/bonito/run.cgi",
        wait=True,
        asyn="0",
        threads=16,
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
        self.db = "".join(["data/", db])
        self.threads = threads

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
        credentials = self._credentials()
        self.calls = sgex.Parse(input).calls
        self._set_wait()
        self._reuse_parameters()
        self._hashes_add()
        self._hashes_compare()
        self._pre_calls()
        manifest = self._make_manifest(credentials)

        local_hosts = ("http://localhost:")
        if  self.server.startswith(local_hosts) and not wait:
            print("... asynchronous")
            self.wait = 0
            self._make_local_calls(manifest)
        else:
            print("... wait =", self.wait)
            self._make_calls(manifest)

        # Close
        self.c.close()
        self.conn.close()

        t1 = time.perf_counter()
        print(f"... {t1 - t0:0.2f} total")