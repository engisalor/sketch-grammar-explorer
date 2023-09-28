"""Utility functions."""
import json

import pandas as pd
import yaml


def flatten_ls_of_dt(ls: list) -> dict:
    """Recursively converts a list of dicts to a dict of lists.

    Notes:
        Returns objects as-is if they're not lists or dicts."""

    def _flatten(ls):
        if not isinstance(ls, list):
            return ls
        else:
            if dict not in [type(x) for x in ls]:
                return ls
            # for [dict, dict, nan] objects
            else:
                # convert nan to empty dict
                ls = [x if isinstance(x, dict) else {} for x in ls]
                # convert list of dicts to dict of lists
                dt = pd.DataFrame(ls).to_dict(orient="list")
                # continue with recursion if needed
                for k, v in dt.items():
                    dt[k] = _flatten(v)
                return dt

    return _flatten(ls)


def parse_json_or_yaml(val: str):
    """Tries to parse a string as JSON, then as YAML."""
    if isinstance(val, str):
        try:
            return json.loads(val)
        except json.decoder.JSONDecodeError:
            return yaml.safe_load(val)
        except Exception as err:
            raise err
    else:
        return val


def read_yaml(file: str) -> dict:
    """Reads a YAML file."""
    with open(file) as stream:
        dt = yaml.safe_load(stream)
    return dt


def read_json(file: str) -> dict:
    """Reads a JSON file."""
    with open(file) as f:
        dt = json.load(f)
    return dt
