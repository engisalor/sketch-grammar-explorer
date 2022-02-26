import pathlib
import json
import yaml

import sgex


class Parse:
    """Parses and returns/saves a JSON/YAML file or dict of API calls.

    `dest="<filepath>"` saves object to file in given format
    - (can be used to convert between file formats)
    """

    def _load(self):

        if not self.input_file.exists():
            raise FileNotFoundError
        else:
            if self.input_file.suffix in [".yml", ".yaml"]:
                with open(self.input_file, "r") as stream:
                    self.calls = yaml.safe_load(stream)
            elif self.input_file.suffix == ".json":
                with open(self.input_file, "r") as f:
                    self.calls = json.load(f)
            else:
                raise ValueError("Unknown format (must be .json .yml .yaml)")

    def _verify(self):
        self.verified = set()
        print(f"... verifying calls")
        if not self.calls:
            self.verified.add(False)
        elif not "type" in self.calls.keys():
            self.verified.add(False)
            raise ValueError('No "type" key in {}'.format(self.input_file))
        elif not self.calls["type"] in self.call_types:
            self.verified.add(False)
            raise ValueError(
                'Unknown call type "{}"\n(must be in {})'.format(
                    self.calls["type"], self.call_types
                )
            )
        else:
            for k, v in self.calls.items():
                if k != "type":
                    if not "call" in v.keys():
                        self.verified.add(False)
                        raise ValueError('No "call" key in "{}"'.format(k))

    def _save(self):
        if not self.output_file:
            raise ValueError("No destination filename")
        else:
            if self.output_file.suffix == ".json":
                with open(self.output_file, "w", encoding="utf-8") as f:
                    json.dump(self.calls, f, ensure_ascii=False, indent=2)
            elif self.output_file.suffix in [".yml", ".yaml"]:
                with open(self.output_file, "w", encoding="utf-8") as f:
                    yaml.dump(
                        self.calls, f, allow_unicode=True, sort_keys=False, indent=2
                    )
            else:
                raise ValueError("Unknown output format: must be .json, .yml, .yaml")

    def _return(self):
        return self.calls

    def __repr__(self):
        return ""

    def __init__(
        self,
        input,
        dest=None,
    ):

        # Variables
        self.calls = None
        self.input_file = None
        if dest:
            self.output_file = pathlib.Path(dest)
        else:
            self.output_file = None

        self.call_types = [k for k in sgex.call_types.keys()]

        # Get input
        if isinstance(input, str):
            self.input_file = pathlib.Path(input)
            self._load()
        elif isinstance(input, dict):
            self.calls = input
        else:
            raise TypeError("Valid inputs: filepath (str) or dict")

        # Execute
        self._verify()

        if not self.output_file:
            self._return()
        else:
            self._save()
