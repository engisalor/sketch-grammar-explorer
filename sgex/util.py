"""Utility functions."""
import json
import re
from urllib import parse

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


def url_from_cql(
    cql: str,
    corpname: str,
    base_url: str = "http://localhost:10070/#concordance?",
    default_attr: str = "lemma_lc",
) -> str:
    """Returns a concordance URL for a given CQL rule, corpus and server.

    Args:
        cql: CQL rule.
        corpname: Corpus name for API access.
        base_url: Server URL to the concordance viewer
        default_attr: CQL default attribute.

    Notes:
        Tested on simple rules so far. Currently limited to viewing concordances.
    """
    params = {
        "corpname": corpname,
        "cql": cql,
        "viewmode": "sen",
        "tab": "advanced",
        "queryselector": "cql",
        "showresults": "1",
        "default_attr": default_attr,
    }
    query = parse.urlencode(params, quote_via=parse.quote)
    base = parse.urlsplit(base_url, allow_fragments=False)
    return base._replace(query=query).geturl()


def detect_cql_type(rule: str) -> str:
    """Categorizes a CQL rule into one of several types.

    Args:
        rule: CQL rule.

    Returns:
        - `ID` if a list of token ids similar to `[#1234|#5678|...]`.
        - `CQL` for anything else.
    """
    r = rule.replace(" ", "")
    _type = []
    if re.match(r"^[ \[\]#\d|]+$", r):
        _type.append("ID")
    else:
        _type.append("CQL")
    if len(_type) != 1:  # QA mechanism for future elif statements
        raise ValueError(f"Error detecting CQL rule type: {_type} for {rule}")
    return _type[0]
