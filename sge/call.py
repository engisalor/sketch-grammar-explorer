import pathlib
import json
import requests
import time
import hashlib
import pandas as pd
from pprint import pprint
import re
import yaml

import sge


class Call:
    """Execute Sketch Engine API calls (saves files and returns class instance).

    Options

    `input` a dictionary or a path to a YAML/JSON file containing API calls
      - if a dict, requires `dest="<destination folder>"`

    `dry_run` make a `Call` object that can be inspected prior to executing requests (`False`)
      - with `job` as an instance of `Call`:
      - `job` prints a summary
      - `job.print_calls()` prints 10 call details at a time
      - `job.calls` accesses all call details

    `skip` skip calls if identical data already exists in the destination folder (`True`)
      - only compares files of the same format
      - note: close data files to ensure read access

    `clear` remove existing data in destination folder before running current calls (`False`)

    `timestamp` include a timestamp (`False`)

    `format` specify output format (`"json"`)

    - `"csv"`, `"txt"`, `"json"`, `"xlsx"`, or `"xml"` (see compatibilities table)
    - `"json"` offers more detailed metadata and API error messages

    `any_format` allow any combination of call types and formats (`False`)

    `asyn` retrieve rough calculations, `"0"` (default) or `"1"`"""

    def _enforce_formats(self):
        """Block known incompatible format and call type combinations."""

        # Set variables
        format = self.global_parameters["format"]
        call_type = self.call_type.strip("?")
        self.bad_format = 'Incompatible call type/format: "{}" + "{}"'.format(
            call_type,
            self.global_parameters["format"],
        )

        # Block non-existant call types
        if not call_type in self.accepted_formats.keys():
            self.format_accepted = False

        # Block known bad combinations
        if call_type in self.accepted_formats.keys():
            if self.accepted_formats[call_type]:
                if format not in self.accepted_formats[call_type]:
                    self.format_accepted = False

    def _credentials(self):
        """Get SkE API credentials from keyring/file.

        Uses hidden config file ".config.yml" if available (for developers).
        Otherwise defaults to "config.yml"
        """

        app = "Sketch Grammar Explorer"
        credentials = None
        path = pathlib.Path("sge/data")
        files = list(path.glob("*config.yml"))
        hidden_config = ".config.yml" in [x.name for x in files]

        if hidden_config:
            file = path / ".config.yml"
        else:
            file = path / "config.yml"

        # Open file
        with open(file, "r") as stream:
            credentials = yaml.safe_load(stream)

        credentials = {k.strip(): v.strip() for k, v in credentials.items()}

        # Try keyring
        if not credentials["api_key"]:
            import keyring

            credentials["api_key"] = keyring.get_password(app, credentials["username"])
        if not credentials["api_key"] or not credentials["username"]:
            raise ValueError("No API key/username found")

        return credentials

    def _version(self):
        """Get SGE version from CITATION.cff."""
        try:
            with open("CITATION.cff", "r") as f:
                lines = f.readlines()

            for x in lines:
                if x.startswith("version:"):
                    version = x

            self.version = version.split(" ")[-1].strip()
        except:
            self.version = "unknown"

    def _hashes_add(self):
        """Add hashes to calls."""

        for i in self.calls.values():
            call_json = json.dumps(i["call"], sort_keys=True)
            call_hash = hashlib.blake2b(call_json.encode()).hexdigest()[0:32]
            i["hash"] = call_hash

    def _hashes_compare(self):
        """Compare hashes, by file format, with existing data in dest_path."""

        hashes = set()
        format = self.global_parameters["format"]
        files = list(self.dest_path.glob("*.{}".format(format)))

        # Get existing hashes by file extension
        for file in files:
            if file.suffix == ".json":
                with open(file, "r") as f:
                    dt = json.load(f)
                hash = dt["request_sge"]["details"]["hash"]
            elif file.suffix in [".csv", ".txt", ".xml"]:
                with open(file, "r") as f:
                    header = f.read()
                hash = re.search("([a-z0-9]{32})", header)[0]
            elif file.suffix == ".xlsx":
                df = pd.read_excel(file, header=None)
                header = df.iloc[0, 0]
                hash = re.search("([a-z0-9]{32})", header)[0]
            else:
                raise ValueError("Unknown file extension")
            hashes.add(hash)

        # Compare hashes and set skip values
        for x in self.calls.values():
            if x["hash"] in hashes:
                x["skip"] = True
            else:
                x["skip"] = False

    def _reuse_parameters(self):
        """Reuse API parameters unless defined explicitly."""

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
        """Set wait time for SkE API usage."""

        n = len(self.calls)
        if n == 1:
            wait = 0
        elif 2 <= n < 100:
            wait = 2
        elif 100 <= n < 900:
            wait = 5
        elif 900 <= n:
            wait = 45

        self.wait = wait

    def _pre_calls(self):
        """Prepare for making calls w/ current parameters."""

        self.url_base = "".join(
            ["https://api.sketchengine.eu/bonito/run.cgi/", self.call_type]
        )

        if self.dry_run:
            print("... DRY-RUN\n{}".format(self))
        else:
            if self.clear and self.dest_path.exists():
                print("... clearing", self.dest_path)
                for f in self.trash:
                    pathlib.Path.unlink(f)

            if self.clear or not self.skip:
                print("... disabling skip")
                for v in self.calls.values():
                    v["skip"] = False

            self.dest_path.mkdir(parents=True, exist_ok=True)

    def _do_call(self, v, k, credentials):
        """Run an api call or skip if existing."""

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

    def _check_response(self):
        """Print API error details when available."""

        if self.global_parameters["format"] == "json":
            if "error" in self.response.json():
                print("... Error API", self.response.json()["error"])

    def _make_header(self):
        """Converts nested dicts with list and str into file header."""

        ls = []
        dt = self.request_sge

        def unpack_dicts(dt):
            for l, w in dt.items():
                if isinstance(w, dict):
                    unpack_dicts(w)
                else:
                    # Make csv/txt lines
                    if self.global_parameters["format"] in ["csv", "txt"]:
                        w = "".join(['"', str(w).replace('"', '""'), '"'])
                        l = "".join(['"', str(l), '"'])
                        ls.append(",".join([l, w]))
                    # Prepare xml elements
                    elif self.global_parameters["format"] == "xml":
                        new_element = l.replace(" ", "_")
                        text = str(w)
                        ls.append([new_element, text])
                    else:
                        raise ValueError("Unknown file extension")

        unpack_dicts(dt)

        # Other modifications
        if self.global_parameters["format"] in ["csv", "txt"]:
            header = "\n".join(ls)
            header = "".join(['"request_sge:",\n', header, "\n"])
        elif self.global_parameters["format"] == "xml":
            header = ls
        return header

    def _save_csv(self):
        header = self._make_header()
        self.response = "".join([self.response.text[0], header, self.response.text[1:]])
        with open(self.file, "w", encoding="utf-8") as f:
            f.write(self.response)

    def _save_json(self):
        self.response = self.response.json()
        del self.response["request"]["username"]
        del self.response["request"]["api_key"]
        self.response["request_sge"] = self.request_sge
        with open(self.file, "w", encoding="utf-8") as f:
            json.dump(self.response, f, ensure_ascii=False, indent=1)

    def _save_txt(self):
        header = self._make_header()
        self.response = "".join([header, self.response.text])
        with open(self.file, "w", encoding="utf-8") as f:
            f.write(self.response)

    def _save_xlsx(self):
        xlsx = pd.read_excel(self.response.content, header=None)
        new_row = "".join(["request_sge", json.dumps(self.request_sge)])
        temp = pd.DataFrame({xlsx.columns[0]: [new_row]})
        temp = temp.append(xlsx)
        temp.to_excel(self.file, header=False, index=False)

    def _save_xml(self):
        from lxml import etree

        xml = etree.fromstring(self.response.content)
        header_old = xml.find("header")
        header = self._make_header()
        request_sge = etree.SubElement(header_old, "request_sge")

        for x in header:
            x[0] = etree.SubElement(request_sge, x[0])
            x[0].text = x[1]

        with open(self.file, "wb") as f:
            f.write(
                etree.tostring(
                    xml,
                    encoding="UTF-8",
                    xml_declaration=True,
                    pretty_print=True,
                )
            )

    def _post_call(self, v, k):
        """Modify and save API response data."""

        suffix = "".join([".", self.global_parameters["format"]])
        file_name = pathlib.Path(k).with_suffix(suffix)
        self.file = self.dest_path / file_name

        self.request_sge = {
            "type": self.call_type[:-1],
            "timestamp": self.timestamp,
            "sge_version": self.version,
            "filename": k,
            "details": v,
        }
        del self.request_sge["details"]["skip"]

        # Parse & save data
        print("... saving to", self.file)
        save_method = "".join(["_save_", self.global_parameters["format"]])
        getattr(Call, save_method)(self)

        # Wait
        print("... waiting", self.wait)
        time.sleep(self.wait)

    def _make_calls(self, credentials):
        """Manage the API call process (pre-call, call, post-call)."""

        self._pre_calls()

        if not self.dry_run:
            for k, v in self.calls.items():
                self._do_call(v, k, credentials)
                if self.response:
                    self._check_response()
                    self._post_call(v, k)

    def print_calls(self):
        """Iteratively print calls in sets of 10."""

        if not hasattr(self, "calls_iterated"):
            items = [(k, v) for k, v in self.calls.items()]
            n = len(items)

            if n <= 10:
                self.calls_iterated = zip(*(iter(items),) * n)
            else:
                self.calls_iterated = zip(*(iter(items),) * 10)

        pprint(next(self.calls_iterated))

    def __repr__(self) -> str:
        """Print job details."""

        trashed = [x.name for x in self.trash]
        skipped = [k for k, v in self.calls.items() if v.get("skip")]
        if self.clear or not self.skip:
            skipped = []

        dt = {
            "input      ": self.input,
            "destination": str(self.dest_path),
            "format     ": self.global_parameters["format"],
            "calls #    ": len(self.calls),
            "wait       ": self.wait,
            "version    ": self.version,
            "timestamp  ": self.timestamp,
            "skip       ": self.skip,
            "skipped #  ": len(skipped),
            "skipped    ": skipped,
            "clear      ": self.clear,
            "cleared #  ": len(trashed),
            "cleared    ": trashed,
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
        any_format=False,
        dest=None,
    ):

        # Settings
        self.accepted_formats = sge.data.call_types
        self.dry_run = dry_run
        self.skip = skip
        self.clear = clear
        self.global_parameters = {"asyn": asyn, "format": format}
        self.format_accepted = True
        self._version()
        if timestamp:
            self.timestamp = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        else:
            self.timestamp = ""

        # Manage input type
        if isinstance(input, str):
            self.dest_path = pathlib.Path(input).with_suffix("")
            self.input = input
        elif isinstance(input, dict):
            if not dest:
                raise ValueError(
                    "Supplying a destination filepath (dest) is required if input is dict"
                )
            else:
                self.dest_path = pathlib.Path(dest).with_suffix("")
                self.input = "object"
        else:
            raise TypeError("Input must be filepath (str) or dict")

        # Prevent using paths outside cwd
        cwd = pathlib.Path.cwd()
        abs_path = cwd / self.dest_path
        if not cwd in abs_path.parents:
            raise ValueError(f"Invalid destination path: \"{self.dest_path}\": paths must be relative to current working directory")
        
        # Execute
        self.trash = []
        if self.clear:
            files = list(self.dest_path.glob("*"))
            suffixes = [".csv", ".json", ".txt", ".xlsx", ".xml"]
            self.trash = [file for file in files if file.suffix in suffixes]

        self.calls = sge.Parse(input).calls
        if not self.calls:
            pass
        else:
            self.call_type = "".join([self.calls["type"], "?"])
            del self.calls["type"]

            if not any_format:
                self._enforce_formats()

            if not self.format_accepted:
                raise ValueError(self.bad_format)
            else:
                credentials = self._credentials()
                self._wait()
                self._reuse_parameters()
                self._hashes_add()
                self._hashes_compare()
                self._make_calls(credentials)
