import pathlib
import json
import requests
import time
import pandas as pd

import sgex

class CallToFile:
    """Executes Sketch Engine API calls, saves in chosen format to (`"data/raw/"`).

    May require `pip install openpyxl lxml`.

    Options

    `input` a dictionary or a path to a YAML/JSON file containing API calls
 
    `dry_run` make a `Call` object that can be inspected prior to executing requests (`False`)
      - `object` prints a summary
      - `job.calls` accesses all call details

     `format` specify output format (`"json"`)
      - `"csv"`, `"txt"`, `"json"`, `"xlsx"`, or `"xml"` 

    `asyn` retrieve rough calculations, `"0"` (default) or `"1"`

    `server` specify what server to call (`"https://api.sketchengine.eu/bonito/run.cgi"`)
      - be sure to omit trailing forward slashes

    `wait` enable waiting between calls (`True`)"""

    def _save_csv(self):
        with open(self.file, "w", encoding="utf-8") as f:
            f.write(self.response.text)

    def _save_json(self):
        self.response = self.response.json()
        del self.response["request"]["username"]
        del self.response["request"]["api_key"]
        with open(self.file, "w", encoding="utf-8") as f:
            json.dump(self.response, f, ensure_ascii=False, indent=1)

    def _save_txt(self):
        with open(self.file, "w", encoding="utf-8") as f:
            f.write(self.response.text)

    def _save_xlsx(self):
        xlsx = pd.read_excel(self.response.content, header=None)
        xlsx.to_excel(self.file, header=False, index=False)

    def _save_xml(self):
        from lxml import etree
        xml = etree.fromstring(self.response.content)

        with open(self.file, "wb") as f:
            f.write(
                etree.tostring(
                    xml,
                    encoding="UTF-8",
                    xml_declaration=True,
                    pretty_print=True,
                )
            )

    def _do_call(self, v, k, credentials):
        """Runs an api call."""

        if self.dry_run:
            pass
        else:
            self.dest_path.mkdir(parents=True, exist_ok=True)
            self.response = None
            parameters = {
                **credentials,
                **self.global_parameters,
                **v["call"],
            }

            t0 = time.perf_counter()
            self.response = requests.get(self.url_base, params=parameters)
            t1 = time.perf_counter()
            print(f"... {t1 - t0:0.2f} secs:", k)
            
            # Error detection
            if not self.response:
                print(f"... bad response: {self.response}")
            elif self.global_parameters["format"] == "json":
                if "error" in self.response.json():
                    error = self.response.json()["error"]
                    print(f"... {t1 - t0:0.2f} secs:", k, "error:", error)
                else:
                    print(f"... {t1 - t0:0.2f} secs:", k)

    def _post_call(self, v, k):
        """Saves API response data."""

        suffix = "".join([".", self.global_parameters["format"]])
        file_name = pathlib.Path(k).with_suffix(suffix)
        self.file = self.dest_path / file_name

        # Parse & save data
        save_method = "".join(["_save_", self.global_parameters["format"]])
        getattr(CallToFile, save_method)(self)

        # Wait
        time.sleep(self.wait)

    def _make_calls(self, credentials):
        """Manages the API call process (do_call, post_call)."""

        if not self.dry_run:
            for k, v in self.calls.items():
                self._do_call(v, k, credentials)
                if self.response:
                    self._post_call(v, k)
    

    def __repr__(self) -> str:
        """Prints job details."""

        dt = {
            "server     ": self.server,
            "input      ": self.input,
            "dest       ": str(self.dest_path),
            "format     ": self.global_parameters["format"],
            "calls      ": len(self.calls),
            "wait       ": self.wait,
        }

        s = [" ".join([k, str(v)]) for k, v in dt.items()]
        s = "\n".join(s)

        return s

    def __init__(
        self,
        input,
        dry_run=False,
        format="json",
        asyn="0",
        server="https://api.sketchengine.eu/bonito/run.cgi",
        wait=True,
    ):

        # Settings
        self.input = input
        self.dry_run = dry_run
        self.global_parameters = {"asyn": asyn, "format": format}
        self.server = server.strip("/")
        self.wait_enabled = wait
        self.dest_path = pathlib.Path("data/raw")

        self.calls = sgex.Parse(input).calls
        if not self.calls:
            pass
        else:
            self.call_type = "".join([self.calls["type"], "?"])
            del self.calls["type"]
            self.url_base = "/".join([self.server, self.call_type])

            credentials = sgex.Call._credentials(self)
            sgex.Call._wait(self)
            sgex.Call._reuse_parameters(self)
            self._make_calls(credentials)
