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
    """Executes Sketch Engine API calls, saves data to sqlite (sgex.db).

    Options

    `input` a dictionary or a path to a YAML/JSON file containing API calls

    `dry_run` make a `Call` object that can be inspected before executing requests (`False`)
      - with `job` as an instance of `Call`:
      - `job` prints a summary
      - `job.calls` accesses all call details

    `skip` skip calls when identical calls already exist in the destination folder (`True`)
      - based on a hash of unique call parameters

    `clear` remove existing data before running current calls (`False`)

    `timestamp` include a timestamp (`False`)

    `format` specify output format (`"json"`)
      - `"json"` available for all call types, includes API error messages
      - `"csv"` available for some call types

    `asyn` retrieve rough calculations, `"0"` (default) or `"1"`

    `server` specify what server to call (`"https://api.sketchengine.eu/bonito/run.cgi"`)
      - must omit trailing forward slashes

    `wait` enable waiting between calls (`True`)"""

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
        """Reuses API parameters unless defined explicitly."""

        ls = [(k, v) for k, v in self.calls.items()]
        for x in range(len(ls)):
            if x == 0:
                pass
            else:
                filename = ls[x][0]
                previous = {**ls[x - 1][1]["call"]}
                current = {**ls[x][1]["call"]}
                self.calls[filename]["call"] = {**previous, **current}

    def _wait(self):
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
        if v["skip"]:
            print("... skipping", k)
        else:
            print("... calling", k)
            parameters = {
                **credentials,
                **self.global_parameters,
                **v["call"],
            }
            self.response = requests.get(self.url_base, params=parameters)
            if not self.response:
                print(f"... bad response: {self.response}")

    def _check_response(self):
        """Prints API error details when available."""

        if self.global_parameters["format"] == "json":
            if "error" in self.response.json():
                print("... Error API", self.response.json()["error"])

    def _post_call(self, v, k):
        """Saves API response data to sqlite database."""

        if self.global_parameters["format"] == "json":
            data = json.dumps(self.response.json())
        elif self.global_parameters["format"] == "csv":
            data = self.response.text
        else:
            print("... Error: unknown format (must be 'json' or 'csv')")

        # Add/replace data
        meta = None
        if "meta" in v.keys():
            if isinstance(v["meta"], (dict, list, tuple)):
                meta = json.dumps(v["meta"], sort_keys=True)
            else:
                meta = v["meta"]

        self.c.execute(
            "INSERT OR REPLACE INTO calls VALUES (?,?,?,?,?,?,?,?)",
            (
                self.input,
                self.call_type[:-1],
                k,
                v["hash"],
                json.dumps(v["call"], sort_keys=True),
                meta,
                self.global_parameters["format"],
                data,
            ),
            )

        self.conn.commit()

        # Wait
        print("... waiting", self.wait)
        time.sleep(self.wait)

    def _make_calls(self, credentials):
        """Manages the API call process (do_call & post_call)."""

        if self.dry_run:
            pass
        else:
            if self.clear:
                print("... clearing")
                self.c.execute("DROP TABLE calls")
                self.conn.commit()
                for x in self.calls.values():
                    x["skip"] = False

            for k, v in self.calls.items():
                self._do_call(v, k, credentials)
                if self.response:
                    self._check_response()
                    self._post_call(v, k)

    def __repr__(self) -> str:
        """Prints job details."""

        dt = {
            "input      ": self.input,
            "server     ": self.server,
            "format     ": self.global_parameters["format"],
            "calls #    ": len(self.calls),
            "wait       ": self.wait,
            "timestamp  ": self.timestamp,
            "skip       ": self.skip,
            "clear      ": self.clear,
        }

        s = [" ".join([k, str(v)]) for k, v in dt.items()]
        s = "\n".join(s)

        return s

    def __init__(
        self,
        input,
        dry_run=False,
        skip=True,
        clear=False,
        timestamp=False,
        format="json",
        asyn="0",
        server="https://api.sketchengine.eu/bonito/run.cgi",
        wait=True,
    ):

        # Settings
        self.dry_run = dry_run
        self.skip = skip
        self.clear = clear
        self.global_parameters = {"asyn": asyn, "format": format}
        self.server = server.strip("/")
        self.wait_enabled = wait
        self.input = "dict"
        self.timestamp = ""

        if timestamp:
            self.timestamp = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(input, str):
            self.input = pathlib.Path(input).name

        # Database
        self.conn = sql.connect("sgex.db")
        self.c = self.conn.cursor()
        self.c.execute(
            """CREATE TABLE IF NOT EXISTS calls (
            input,
            type text,
            id text,
            hash text UNIQUE,
            call text,
            meta text,
            format text,
            response text)"""
        )

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
