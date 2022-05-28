import pathlib
import json
import requests
import time
import hashlib
import datetime
import yaml
import sqlite3 as sql
from concurrent.futures import ThreadPoolExecutor
import os
import logging
from logging.handlers import TimedRotatingFileHandler
import sys
import shutil

import sgex

targets = logging.StreamHandler(sys.stdout), TimedRotatingFileHandler(
    ".sgex.log", backupCount=1
)
logging.basicConfig(
    encoding="utf-8",
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    datefmt="%Y-%m-%d %I:%M:%S",
    handlers=targets,
)
logger = logging.getLogger()


class Call:
    """Executes Sketch Engine API calls & saves data to desired output.

    Options

    `input` a dictionary or path to a YAML/JSON file containing API calls

    `output` save to sqlite (default `sgex.db`) or files: `json`, `csv`, `xlsx`, `xml`, `txt`

    `dry_run` (`False`)

    `skip` skip calls when a hash of the same parameters already exists in sqlite (`True`)

    `clear` remove existing data before calls (sqlite table or `data/raw/`) (`False`)

    `server` select a server from `config.yml` (`"ske"`)

    `threads` for asynchronous calling (`None` for default, otherwise an integer)

    `progress` print call progress (`True`)

    `loglevel` (`"info"`) outputs to `.sgex.log`"""

    def _get_config(self):
        """Gets servers and credentials config file.

        Hidden version has priority if both; generates a file if none."""

        if pathlib.Path(self.config_file_default).exists():
            self.config_file = self.config_file_default
        elif pathlib.Path(self.config_file_default[1:]).exists():
            self.config_file = self.config_file_default[1:]
        if self.config_file:
            logging.debug(f"CONFIG {self.config_file}")
            with open(self.config_file, "r") as stream:
                config = yaml.safe_load(stream)
        else:
            with open(self.config_file_default[1:], "w", encoding="utf-8") as f:
                default = {
                    "noske": {
                        "server": "http://localhost:10070/bonito/run.cgi",
                        "asynchronous": True,
                        },
                    "ske": {
                        "api_key": "key",
                        "server": "https://api.sketchengine.eu/bonito/run.cgi",
                        "username": "user",
                        "wait": {0: 1, 2: 99, 5: 899, 45: None},
                    },
                }
                yaml.dump(default, f, allow_unicode=True, indent=2)
            raise FileNotFoundError(
                """
        Sketch Grammar Explorer

        No config file detected: generating 'config.yml' - add credentials, then try again."

        If a server requires credentials, add 'username' and 'api_key' to server info.
        API keys can also be managed in the OS keyring with these commands:

            sgex.config.keyring_add_key()
            sgex.config.keyring_delete_key()

        If using keyring to store an API key, leave 'api_key' empty or set as null.

        See documentation at https://github.com/engisalor/sketch-grammar-explorer"""
            )

        return config

    def _get_server_info(self, server, config):
        """Gets API credentials and other settings for a SkE server."""

        server_info = config.get(server)
        if not server_info:
            raise KeyError(f'No credentials for {server} in "{self.config_file}"')

        # Manage username & API key
        if not "username" in server_info:
            logging.debug(f"CREDS anonymous")
        elif "api_key" in server_info and not server_info.get("api_key"):
            logging.debug("CREDS keyring")
            if not server_info.get("username"):
                raise ValueError("No username found for {server}")
            else:
                import keyring

                api_key = keyring.get_password(
                    server_info["server"], server_info["username"]
                )
            if not api_key:
                raise ValueError(
                    f'No API key found in keyring for user {server_info["username"]}'
                )
            else:
                server_info["api_key"] = api_key
        else:
            logging.debug("CREDS plaintext")

        return server_info

    def _hashes_add(self):
        """Adds hashes to calls."""

        for i in self.calls.values():
            call_json = json.dumps(i["call"], sort_keys=True)
            i["hash"] = hashlib.blake2b(call_json.encode()).hexdigest()[0:32]

    def _hashes_compare(self):
        """Compares hashes with existing data, sets skip values."""

        for x in self.calls.values():
            self.c.execute("select hash from calls where hash=?", (x["hash"],))
            if self.c.fetchone() and self.skip:
                x["skip"] = True
            else:
                x["skip"] = False

    def _reuse_parameters(self):
        """Reuses parameters unless defined explicitly.

        Parameters are reused for sequential calls of the same type. If `type`
        is specified, nothing is reused. Otherwise, when a parameter changes,
        it will be reused until redefined again in a later call.

        If parameters are part of a dictionary, individual key:values are reused.
        Otherwise, the item is replaced flatly."""

        def _log_entry(self, curr, action, k):
            self.log_entry[curr].extend([action, k])

        def _propagate(self, ids, k):
            for x in range(len(ids)):
                prev = ids[x - 1]
                curr = ids[x]

                if "type" in self.calls[curr] or x == 0:
                    _log_entry(self, curr, " skip:", k)
                elif isinstance(self.calls[prev].get(k), dict) and isinstance(
                    self.calls[curr].get(k), dict
                ):
                    self.calls[curr][k] = {
                        **self.calls[prev].get(k),
                        **self.calls[curr].get(k),
                    }
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
        [logging.debug(f'{" ".join(v)}    {k}') for k, v in self.log_entry.items()]
        self.calls = self.calls

    def _set_wait(self, server_info):
        """Sets wait time for server usage (if wait provided in config file)."""

        if not "wait" in server_info:
            self.wait = 0
        else:
            n = len(self.calls)
            waits = []
            for k, v in server_info["wait"].items():
                if v:
                    if n <= v:
                        waits.append(k)
            if not waits:
                waits.append(max([k for k in server_info["wait"].keys()]))
            self.wait = min(waits)

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
            if credentials.get("api_key"):
                logging.debug(
                    f'REQUEST {req.url.replace(credentials["api_key"],"REDACTED")}'
                )
            else:
                logging.debug(f"REQUEST {req.url}")

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
        """Runs calls in manifest asynchronously (when using a local server)."""

        THREAD_POOL = self.threads
        session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(
            pool_maxsize=THREAD_POOL, pool_block=True
        )
        session.mount("http://", adapter)

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
                elif isinstance(keep, (list, tuple)):
                    keeps = keep
                else:
                    raise TypeError(
                        f'Bad type for "keep" {type(keep)}: use string, list, tuple'
                    )
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
        import pandas as pd

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
        server="ske",
        threads=None,
        progress=True,
        loglevel="info",
    ):
        # Settings
        self.dry_run = dry_run
        self.skip = skip
        self.clear = clear
        self.threads = min(32, os.cpu_count() + 4)
        self.progress = progress
        self.timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.input = "dict"
        self.db_extensions = ".db"
        self.errors = []
        self.supported_formats = ["csv", "json", "txt", "xml", "xlsx"]
        self.config_file = None
        self.config_file_default = ".config.yml"
        if isinstance(input, str):
            self.input = pathlib.Path(input).name
        if threads:
            self.threads = threads

        # Logging
        logging.info(f"START sgex.Call {self.input}")
        numeric_level = getattr(logging, loglevel.upper(), None)

        if not isinstance(numeric_level, int):
            raise ValueError("Invalid log level: %s" % loglevel)
        logger.setLevel(numeric_level)

        if dry_run and loglevel != "debug":
            handlers = logger.handlers
            logger.removeHandler(handlers[-1])

        # Prepare
        t0 = time.perf_counter()
        pathlib.Path.mkdir(pathlib.Path("data"), exist_ok=True)
        config = self._get_config()
        server_info = self._get_server_info(server, config)
        self.server = server_info.get("server").strip("/")
        self.calls = sgex.Parse(input).calls
        self._reuse_parameters()
        self._set_wait(server_info)
        credentials = {
            k: v for k, v in server_info.items() if k in ["username", "api_key"]
        }

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
            raise ValueError(
                f'{output} not a recognized output, e.g.: "project.db" or "json"'
            )

        # Queue calls
        self._pre_calls()
        manifest = self._make_manifest(credentials)
        self.queued = len(manifest)
        logging.info(f"QUEUED {self.queued} / {len(self.calls)}")

        # Call mode
        if server_info.get("asynchronous"):
            self.mode = "asynchronous"
        else:
            self.mode = "sequential"
        logging.info(f"SERVER {self.mode}")

        # Execute
        if manifest and not self.dry_run and self.mode == "asynchronous":
            self._make_local_calls(manifest)
        elif manifest and not self.dry_run:
            self._make_calls(manifest)
        else:
            pass

        if manifest and not self.dry_run:
            self.called = len(manifest)
        else:
            self.called = 0
        t1 = time.perf_counter()
        logging.info(f"CALLED {self.called} in {t1 - t0:0.2f} secs")

        # Wrap up
        if output.endswith(self.db_extensions):
            self.c.execute("pragma optimize")
            self.c.close()
            self.conn.close()
        if self.errors:
            logging.warning(f"ERRORS {len(self.errors)} {set(self.errors)}")
        [logging.info(f"{k}{v}") for k, v in self.summary().items()]
