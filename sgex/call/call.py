"""Functions for preparing lists of Calls prior to making requests."""
import json
import re
from hashlib import blake2b
from urllib.parse import parse_qs, urlparse

from requests import PreparedRequest, Request

from sgex.config import credential_parameters


def prepare(calls: list, server: str, conf: dict, **kwargs) -> None:
    """Prepares a list of Calls to send (propagates params, creates Request object)."""
    creds = {k: v for k, v in conf[server].items() if k in credential_parameters}
    propagate(calls)
    for call in calls:
        call.validate()
    add_creds(calls, creds)
    add_request(calls, server, conf, **kwargs)
    add_key(calls)


def propagate_key(calls: list, key: str) -> None:
    """Propagates parameters for one key in a list of Calls."""
    for x in range(1, len(calls)):
        # ignore if type changes
        if calls[x].type != calls[x - 1].type:
            pass
        # merge if value is a dict
        elif isinstance(calls[x - 1].params.get(key), dict) and isinstance(
            calls[x].params.get(key), dict
        ):
            calls[x].params[key] = {
                **calls[x - 1].params.get(key),
                **calls[x].params.get(key),
            }
        # ignore existing non-dict values
        elif calls[x].params.get(key):
            pass
        # reuse missing non-dict values
        elif calls[x - 1].params.get(key):
            calls[x].params[key] = calls[x - 1].params.get(key)
        else:
            pass


def propagate(calls: list) -> None:
    """Propagates (recycles) parameters for all keys in a list of Calls."""
    keys = set([k for call in calls for k in call.params.keys()])
    for k in keys:
        propagate_key(calls, k)
    return calls


def add_creds(calls: list, creds: dict) -> None:
    """Adds credentials to parameters for a list of Calls."""
    for x in range(len(calls)):
        calls[x].params = {**creds, **calls[x].params}


def add_request(calls: list, server: str, conf, **kwargs) -> None:
    """Generates Request objects for a list of calls."""
    for x in range(len(calls)):
        calls[x].request = Request(
            "GET",
            url="/".join([conf[server]["host"], calls[x].type]),
            params=calls[x].params,
            **kwargs,
        )


def normalize_dt(dt: dict):
    """Normalizes a dictionary of parameters."""
    return {k.strip(): normalize_values(v) for k, v in dt.items()}


def normalize_values(value: any) -> any:
    """Normalizes values for a dictionary of parameters."""
    if isinstance(value, str):
        value = value.strip()
    elif isinstance(value, list):
        value = [normalize_values(x) for x in value]
        value.sort()
    elif isinstance(value, dict):
        value = normalize_dt(value)
    else:
        pass
    return value


def create_custom_key(
    request: PreparedRequest,
    ignored_parameters: list = credential_parameters,
    **kwargs,
) -> str:
    """Generates a custom key for requests-cache based request type and parameters."""
    # TODO improve standardization of CQL rule strings e.g. extra spaces within content
    params = parse_qs(urlparse(request.url).query)
    params_redacted = {k: v for k, v in params.items() if k not in ignored_parameters}
    params_normalized = normalize_dt(params_redacted)
    type = {"type": re.search(r"run.cgi/(.*)\?", request.url).group(1)}
    params_with_type = {**type, **params_normalized}
    params_json = json.dumps(params_with_type, sort_keys=True)
    key = blake2b(digest_size=8)
    key.update(params_json.encode())
    return key.hexdigest()


def add_key(calls: list, **kwargs) -> None:
    """Generates keys for a list of Calls."""
    for x in range(len(calls)):
        calls[x].key = create_custom_key(
            calls[x].request.prepare(),
            ignored_parameters=credential_parameters,
            **kwargs,
        )
