import json
import os
import pathlib

from sgex import io

default = {
    "noske": {
        "server": "http://localhost:10070/bonito/run.cgi",
        "asynchronous": True,
    },
    "ske": {
        "api_key": "<key>",
        "server": "https://api.sketchengine.eu/bonito/run.cgi",
        "username": "<user>",
        "wait": {"0": 1, "2": 99, "5": 899, "45": None},
    },
}


def from_file(file: str) -> dict:
    file = pathlib.Path(file)
    if file.suffix in [".yml", ".yaml"]:
        dt = io.read_yaml(file)
    elif file.suffix in [".json"]:
        dt = io.read_json(file)
    else:
        raise ValueError("file format must be .yml, .yaml, or .json")
    return dt


def from_str(s: str) -> dict:
    return json.loads(s)


def from_env(var: str = "SGEX_CONFIG_JSON") -> dict:
    s = os.environ.get(var)
    return from_str(s)


def load(source: str, keyring: bool = False, **kwargs) -> dict:
    if isinstance(source, dict):
        conf = source
    elif source.endswith((".yml", ".yaml", ".json")):
        conf = from_file(source)
    elif source.isupper():
        conf = from_env(source)
    else:
        conf = from_str(source)
    if keyring:
        conf = read_keyring(conf, **kwargs)
    return conf


def read_keyring(  # nosec
    conf, server: str, id_key: str = "username", password_key: str = "api_key"
) -> dict:
    import keyring

    p = keyring.get_password(conf[server]["host"], conf[server][id_key])
    conf[server][password_key] = p
    return conf
