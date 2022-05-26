import pathlib
import json
import requests
import time
import hashlib
import pandas as pd
import yaml
import sqlite3 as sql
from concurrent.futures import ThreadPoolExecutor
import os

import sgex


class Call:
    """Executes Sketch Engine API calls & saves data to sqlite database.

    Options

    `input` a dictionary or path to a YAML/JSON file containing API calls

    `output` save to sqlite (default `sgex.db`) or files: `json`, `csv`, `xlsx`, `xml`, `txt`

    `dry_run` make a `Call` object without executing requests (`False`)

    `skip` skip calls when a hash of the same parameters already exists in sqlite (`True`)

    `clear` remove existing sqlite data before running current calls (`False`)

    `server` (`"https://api.sketchengine.eu/bonito/run.cgi"`)

    `wait` wait between calls (`True`) (follows SkE wait policy)

    `threads` for asynchronous calling (`None` for default, otherwise an integer)

    `asyn` retrieve rough calculations, `"0"` (default) or `"1"`
    
    `progress` print call progress (`True`)"""

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

        def _propagate(self, ids, k):
            for x in range(len(ids)):
                prev = ids[x - 1]
                curr = ids[x]

                if "type" in self.calls[curr] or x == 0:
                    logging.debug(f"ignore  {k} {curr}")
                elif isinstance(self.calls[prev].get(k), dict) and isinstance(self.calls[curr].get(k), dict):
                    self.calls[curr][k] = {**self.calls[prev].get(k),**self.calls[curr].get(k)}
                    logging.debug(f"combine {k} {curr}")
                elif self.calls[curr].get(k):
                    pass
                    logging.debug(f"ignore  {k} {curr}")
                elif self.calls[prev].get(k):
                    self.calls[curr][k] = self.calls[prev].get(k)
                    logging.debug(f"reuse   {k} {curr}")
                    else:
                    logging.debug(f"ignore  {k} {curr}")
       
        logging.debug(f"REUSING parameters")
        ids = list(self.calls.keys())
        [_propagate(self, ids, k) for k in ["meta", "keep", "call"]]
        _propagate(self, ids, "type")
        self.calls = self.calls

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
            "https://",
            requests.adapters.HTTPAdapter(
                pool_maxsize=THREAD_POOL,
                                        # max_retries=3,
                pool_block=True,
            ),
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
            print("Bad response:", packet["response"])
            self.errors.append(packet["response"])
        else:
            # Error handling
            if self.global_parameters["format"] == "json":
                self.data = json.dumps(packet["response"].json())
                error = None
                if "error" in packet["response"].json():
                    error = packet["response"].json()["error"]
                    self.errors.append(error)
            
            # SQLite
            if self.output.endswith(self.db_extensions):
                # Keep data
                if "keep" in packet["item"]["params"]:
                    keep = packet["item"]["params"]["keep"]
                    if isinstance(keep, str):
                        keeps = [keep]
                    kept = {
                        k: v for k, v in packet["response"].json().items() if k in keeps
                    }
                    self.data = json.dumps(kept)

                # Add metadata
                meta = None
                if "meta" in packet["item"]["params"].keys():
                    if isinstance(
                        packet["item"]["params"]["meta"], (dict, list, tuple)
                    ):
                        meta = json.dumps(
                            packet["item"]["params"]["meta"], sort_keys=True
                        )
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
                        self.data,
                    ),
                    )
                self.conn.commit()
            
            # Filesystem
            else:                
                # Save to specified format
                self.data = packet["response"]
                dir = pathlib.Path(self.output)
                name = pathlib.Path(packet["item"]["id"]).with_suffix(self.extension)
                self.file = dir / name
                save_method = "".join(["_save_", self.global_parameters["format"]])
                getattr(Call, save_method)(self)

    def _save_csv(self):
        with open(self.file, "w", encoding="utf-8") as f:
            f.write(self.data.text)

    def _save_json(self):
        self.data = self.data.json()
        del self.data["request"]["username"]
        del self.data["request"]["api_key"]
        with open(self.file, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=1)

    def _save_txt(self):
        with open(self.file, "w", encoding="utf-8") as f:
            f.write(self.data.text)

    def _save_xlsx(self):
        xlsx = pd.read_excel(self.data.content, header=None)
        xlsx.to_excel(self.file, header=False, index=False)

    def _save_xml(self):
        from lxml import etree

        xml = etree.fromstring(self.data.content)

        with open(self.file, "wb") as f:
            f.write(
                etree.tostring(
                    xml,
                    encoding="UTF-8",
                    xml_declaration=True,
                    pretty_print=True,
                )
            )

    def _print_progress(self, response, manifest_item):
        if self.progress:
            error = ""
            if self.global_parameters["format"] == "json":
                if "error" in response.json():
                    error = response.json()["error"]
            print(f"{self.t1 - self.t0:0.2f}", manifest_item["id"], error)

    def _pre_calls(self):
        if self.dry_run:
            for x in self.calls.values():
                x["skip"] = True
        else:
            if self.clear and self.output.endswith(self.db_extensions):
                ts = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
                print(ts, f"CLEAR  {self.output}")
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
            "\nDETAILS  ": "",
            "input      ": self.input,
            "output     ": self.output,
            "format     ": self.global_parameters["format"],
            "skip       ": self.skip,
            "clear      ": self.clear,
            "server     ": self.server,
            "wait       ": self.wait,
            "threads    ": self.threads,
            "asyn       ": self.global_parameters["asyn"],
            "progress   ": self.progress,
        }

        s = [" ".join([k, str(v)]) for k, v in dt.items()]
        s = "\n".join(s)

        return s

    def __init__(
        self,
        input,
        output="sgex.db",
        dry_run=False,
        skip=True,
        clear=False,
        server="https://api.sketchengine.eu/bonito/run.cgi",
        wait=True,
        asyn="0",
        threads=None,
        progress=True,
    ):
        # Settings
        self.dry_run = dry_run
        self.skip = skip
        self.clear = clear
        self.server = server.strip("/")
        self.wait_enabled = wait
        self.timestamp = None
        self.global_parameters = {"asyn": asyn}
        self.threads = min(32, os.cpu_count() + 4)
        self.progress = progress
        self.timestamp = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        self.input = "dict"
        self.db_extensions = (".db")
        self.errors = []
        if isinstance(input, str):
            self.input = pathlib.Path(input).name
        if threads:
            self.threads = threads

        t0 = time.perf_counter()
        print(self.timestamp, f"START  {self.input}")

        pathlib.Path.mkdir(pathlib.Path("data"), exist_ok=True)
        # Database
        if output.endswith(self.db_extensions):
            self.output = "".join(["data/", output])
            self.conn = sql.connect(self.output)
            self.c = self.conn.cursor()
            self._make_table()
            self.global_parameters["format"] = "json"
        # Filesystem
        else:
            self.output = "data/raw"
            self.extension = "".join([".", output.strip(".")])
            self.global_parameters["format"] = output.strip(".")
            pathlib.Path.mkdir(pathlib.Path(self.output), exist_ok=True)

        # Prepare
        credentials = self._credentials()
        self.calls = sgex.Parse(input).calls
        self._set_wait()
        self._reuse_parameters()

        # SQLite
        if output.endswith(self.db_extensions):
            self._hashes_add()
            self._hashes_compare()
        # Filesystem
        else:
            for x in self.calls.values():
                x["skip"] = False

        self._pre_calls()
        manifest = self._make_manifest(credentials)
        ts = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        print(ts, f"QUEUED {len(manifest)} / {len(self.calls)}")

        # Execute
        if manifest:
            local_hosts = "http://localhost:"
            if self.server.startswith(local_hosts) and not wait:
                self.wait = 0
                self._make_local_calls(manifest)
            else:
                self._make_calls(manifest)
        
        # Wrap up
        if output.endswith(self.db_extensions):
            self.c.close()
            self.conn.close()

        t1 = time.perf_counter()
        ts = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        print(ts, f"CALLED {len(manifest)} in {t1 - t0:0.2f} secs")
 
        if self.global_parameters["format"] == "json":
            print(ts, f"ERRORS {len(self.errors)} {set(self.errors)}")
        else:
            print(ts, f"ERRORS NA")
