"""Functions for preparing lists of Calls prior to making requests."""
import json
from hashlib import blake2b
from urllib.parse import parse_qs, urlparse

from requests import PreparedRequest, Request

from sgex.call.type import Call
from sgex.config import ignored_parameters


def prepare(calls: list[Call], server: str, conf: dict, **kwargs) -> None:
    """Prepares a list of Calls to send (propagates params, creates Request object)."""
    creds = {k: v for k, v in conf[server].items() if k in ignored_parameters}
    propagate(calls)
    for call in calls:
        call.validate()
    add_creds(calls, creds)
    add_request(calls, server, conf, **kwargs)
    add_key(calls)


def propagate_key(calls: list[Call], key: str) -> None:
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


def propagate(calls: list[Call]) -> None:
    """Propagates (recycles) parameters for all keys in a list of Calls."""
    keys = set([k for call in calls for k in call.params.keys()])
    for k in keys:
        propagate_key(calls, k)
    return calls


def add_creds(calls: list[Call], creds: dict) -> None:
    """Adds credentials to parameters for a list of Calls."""
    for x in range(len(calls)):
        calls[x].params = {**creds, **calls[x].params}


def add_request(calls: list[Call], server: str, conf, **kwargs) -> None:
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


def create_key_from_params(
    request: PreparedRequest,
    ignored_parameters: list = [],
    **kwargs,
) -> str:
    """Generates a custom key for requests-cache based solely on request parameters."""
    params = parse_qs(urlparse(request.url).query)
    params_redacted = {k: v for k, v in params.items() if k not in ignored_parameters}
    params_normalized = normalize_dt(params_redacted)
    params_json = json.dumps(params_normalized, sort_keys=True)
    key = blake2b(digest_size=8)
    key.update(params_json.encode())
    return key.hexdigest()


def add_key(calls: list[Call], **kwargs) -> None:
    """Generates keys for a list of Calls."""
    for x in range(len(calls)):
        calls[x].key = create_key_from_params(
            calls[x].request.prepare(),
            ignored_parameters=ignored_parameters,
            **kwargs,
        )
