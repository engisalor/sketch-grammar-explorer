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
import logging
from logging.handlers import TimedRotatingFileHandler
import sys
import shutil

import sgex

targets = logging.StreamHandler(sys.stdout), TimedRotatingFileHandler('.sgex.log', backupCount=1)
logging.basicConfig(
    encoding='utf-8', 
    level=logging.INFO, 
    format='%(asctime)s %(message)s',
    datefmt='%Y-%m-%d %I:%M:%S',
    handlers=targets,
    )
logger = logging.getLogger()


class Call:
    """Executes Sketch Engine API calls & saves data to sqlite database.

    Options

    `input` a dictionary or path to a YAML/JSON file containing API calls

    `output` save to sqlite (default `sgex.db`) or files: `json`, `csv`, `xlsx`, `xml`, `txt`

    `dry_run` (`False`)

    `skip` skip calls when a hash of the same parameters already exists in sqlite (`True`)

    `clear` remove existing data before calls (sqlite table or `data/raw/`) (`False`)

    `server` (`"https://api.sketchengine.eu/bonito/run.cgi"`)

    `wait` `None` bases policy on server type (`False` if localhost, otherwise `True`) - override with boolean

    `threads` for asynchronous calling (`None` for default, otherwise an integer)

    `progress` print call progress (`True`)
    
    `loglevel` (`"info"`) see `.sgex.log`"""

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

        for x in self.calls.values():
            self.c.execute("select hash from calls where hash=?",(x["hash"],))
            if self.c.fetchone() and self.skip:
                x["skip"] = True
            else: x["skip"] = False

    def _reuse_parameters(self):
        """Reuses parameters unless defined explicitly.
        
        Parameters are reused for sequential calls of the same type. If `type`
        is specified, nothing is reused. Otherwise, when a parameter changes,
        it will be reused until redefined again in a later call.

        If parameters are part of a dictionary, individual key:values are reused.
        Otherwise, the item is replaced flatly."""

        def _log_entry(self, curr, action, k):
            self.log_entry[curr].extend([action,k])

        def _propagate(self, ids, k):
            for x in range(len(ids)):
                prev = ids[x - 1]
                curr = ids[x]

                if "type" in self.calls[curr] or x == 0:
                    _log_entry(self, curr, " skip:", k)
                elif isinstance(self.calls[prev].get(k), dict) and isinstance(self.calls[curr].get(k), dict):
                    self.calls[curr][k] = {**self.calls[prev].get(k),**self.calls[curr].get(k)}
                    _log_entry(self, curr, " comb:", k)
                elif self.calls[curr].get(k):
                    pass
                    _log_entry(self, curr, " skip:", k)
                elif self.calls[prev].get(k):
                    self.calls[curr][k] = self.calls[prev].get(k)
                    _log_entry(self, curr, "reuse:", k)
                else:
                    _log_entry(self, curr, " skip:", k)


        ids = list(self.calls.keys())
        self.log_entry = {id: ["PARAMS  "] for id in ids}
        [_propagate(self, ids, k) for k in ["call", "meta", "keep", "type"]]
        [logging.debug(f'{" ".join(v)}    {k}') for k,v in self.log_entry.items()]
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
            parameters = {
                **credentials,
                **{"format": self.format},
                **v["call"],
            }

            call_type = "".join([v["type"], "?"])
            url_base = "/".join([self.server, call_type])
            req.prepare_url(url_base, parameters)

            if not v["skip"]:
                manifest.append({"id": k, "params": v, "url": req.url})
            
            logging.debug(f'REQUEST {req.url.replace(credentials["api_key"],"REDACTED")}')

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

        packet["response"].raise_for_status()
    
        if self.format == "json":
            # Keep data
            if "keep" in packet["item"]["params"]:
                keep = packet["item"]["params"]["keep"]
                if isinstance(keep, str):
                    keeps = [keep]
                kept = {
                    k: v for k, v in packet["response"].json().items() if k in keeps
                }
                self.data = kept
            else:
                self.data = packet["response"].json()
            # Scrub credentials            
            if "request" in self.data:
                for i in ["api_key", "username"]:
                    if i in self.data["request"]:
                        del self.data["request"][i]
            # API errors
            error = None
            if "error" in packet["response"].json():
                error = packet["response"].json()["error"]
                self.errors.append(error)
        
        # SQLite
        if self.output.endswith(self.db_extensions):
            # Add metadata
            meta = None
            if "meta" in packet["item"]["params"]:
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
                    json.dumps(self.data),
                ),
                )
            self.conn.commit()
        
        # Filesystem
        else:                
            # Save to specified format
            if not self.format == "json":
                self.data = packet["response"]
            dir = pathlib.Path(self.output)
            name = pathlib.Path(packet["item"]["id"]).with_suffix(self.extension)
            self.file = dir / name
            save_method = "".join(["_save_", self.format])
            getattr(Call, save_method)(self)

    def _save_csv(self):
        with open(self.file, "w", encoding="utf-8") as f:
            f.write(self.data.text)

    def _save_json(self):
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
            if self.format == "json":
                if "error" in response.json():
                    error = response.json()["error"]
            logging.info(f'{self.t1 - self.t0:0.2f} {manifest_item["id"]} {error}')

    def _pre_calls(self):
        if self.clear and self.output.endswith(self.db_extensions):
            logging.info(f"CLEAR {self.output}")
            self.c.execute("DROP TABLE calls")
            self._make_table()
            self.conn.commit()
            for x in self.calls.values():
                x["skip"] = False
        elif self.clear and self.output == "data/raw":
            logging.info(f"CLEAR {self.output}")
            shutil.rmtree(self.output)
            pathlib.Path.mkdir(pathlib.Path(self.output), exist_ok=True)

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

    def summary(self):
        return {
            "input      ": self.input,
            "output     ": self.output,
            "format     ": self.format,
            "skip       ": self.skip,
            "clear      ": self.clear,
            "server     ": self.server,
            "wait       ": self.wait,
            "threads    ": self.threads,
            "progress   ": self.progress,
        }

    def __repr__(self):
        return ""

    def __init__(
        self,
        input,
        output="sgex.db",
        dry_run=False,
        skip=True,
        clear=False,
        server="https://api.sketchengine.eu/bonito/run.cgi",
        wait=None,
        threads=None,
        progress=True,
        loglevel="info",
    ):
        # Settings
        self.dry_run = dry_run
        self.skip = skip
        self.clear = clear
        self.server = server.strip("/")
        self.threads = min(32, os.cpu_count() + 4)
        self.progress = progress
        self.timestamp = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        self.input = "dict" 
        self.db_extensions = (".db")
        self.errors = []
        self.supported_formats = ["csv", "json", "txt", "xml", "xlsx"]
        local_host = "http://localhost:"
        if isinstance(input, str):
            self.input = pathlib.Path(input).name
        if threads:
            self.threads = threads

        # Enable wait
        if wait is None:
            if self.server.startswith(local_host):
                self.wait_enabled = False
            else:
                self.wait_enabled = True
        elif wait is False:
            self.wait_enabled = False
        elif wait is True:
            self.wait_enabled = True
        else:
            raise ValueError(f'Bad wait value {self.wait}: must be None, True, False')

        # Logging
        logging.info(f"START sgex.Call {self.input}")        
        numeric_level = getattr(logging, loglevel.upper(), None)

        if not isinstance(numeric_level, int):
            raise ValueError('Invalid log level: %s' % loglevel)
        logger.setLevel(numeric_level)

        if dry_run and loglevel != "debug":
            handlers = logger.handlers
            logger.removeHandler(handlers[-1])
        
        # Prepare
        t0 = time.perf_counter()
        pathlib.Path.mkdir(pathlib.Path("data"), exist_ok=True)
        credentials = self._credentials()
        self.calls = sgex.Parse(input).calls
        self._set_wait()
        self._reuse_parameters()

        # SQLite
        if output.endswith(self.db_extensions):
            self.output = "".join(["data/", output])
            self.conn = sql.connect(self.output)
            self.c = self.conn.cursor()
            self._make_table()
            self.format = "json"
            self._hashes_add()
            self._hashes_compare()
        # Filesystem
        elif output in self.supported_formats:
            self.output = "data/raw"
            self.extension = "".join([".", output.strip(".")])
            self.format = output.strip(".")
            pathlib.Path.mkdir(pathlib.Path(self.output), exist_ok=True)
            for x in self.calls.values():
                x["skip"] = False
        else:
            raise ValueError(f'{output} not a recognized output, e.g.: "project.db" or "json"')

        # Execute
        self._pre_calls()
        manifest = self._make_manifest(credentials)
        self.queued = len(manifest)
        logging.info(f"QUEUED {self.queued} / {len(self.calls)}")

        if manifest and not self.dry_run:
            if self.server.startswith(local_host):
                self.wait = 0
                self._make_local_calls(manifest)
            else:
                self._make_calls(manifest)
        
        # Wrap up
        if output.endswith(self.db_extensions):
            self.c.close()
            self.conn.close()

        t1 = time.perf_counter()
        logging.info(f"CALLED {len(manifest)} in {t1 - t0:0.2f} secs")
        if self.errors:
            logging.warning(f"ERRORS {len(self.errors)} {set(self.errors)}")
        [logging.info(f"{k}{v}") for k,v in self.summary().items()]
