"""Default settings and functions to load configuration data."""
import json
import os
import pathlib

from sgex import io

# default server configuration
default = {
    "noske": {
        "host": "http://localhost:10070/bonito/run.cgi",
        "asynchronous": True,
    },
    "ske": {
        "api_key": "<key>",
        "host": "https://api.sketchengine.eu/bonito/run.cgi",
        "username": "<user>",
        "wait": {"0": 1, "2": 99, "5": 899, "45": None},
    },
}

# accepted return formats (SkE default is "json")
formats = ["json", "xml", "xlsx", "csv", "txt"]

# parameters to exclude from requests_cache functions
credential_parameters = ["api_key", "username"]


def from_file(file: str) -> dict:
    """Loads configuration from a YAML or JSON file."""
    file = pathlib.Path(file)
    if file.suffix in [".yml", ".yaml"]:
        dt = io.read_yaml(file)
    elif file.suffix in [".json"]:
        dt = io.read_json(file)
    else:
        raise ValueError("file format must be .yml, .yaml, or .json")
    return dt


def from_str(s: str) -> dict:
    """Loads configuration from a JSON-formatted string."""
    return json.loads(s)


def from_env(var: str = "SGEX_CONFIG_JSON") -> dict:
    """Loads configuration from an environment variable (a JSON-formatted string)."""
    s = os.environ.get(var)
    return from_str(s)


def load(source: str) -> dict:
    """Loads configuration from any available source.

    Args:
        source: Can be any of the following:
            a dictionary (see ``sgex.config.default`` for an example);
            a filepath to a JSON/YAML configuration file (``config.yml``);
            the name of a JSON-formatted environment variable (``SGEX_CONFIG_JSON``);
            a JSON-formatted string (``"{<JSON content>}"``).

    Notes:
        If multiple source types exist, priority is given in this order:
            dict, env, filepath, str.
    """
    if isinstance(source, dict):
        return source
    elif source.isupper():
        return from_env(source)
    elif source.endswith((".yml", ".yaml", ".json")):
        return from_file(source)
    else:
        return from_str(source)


def read_keyring(conf: dict, server: str) -> dict:
    """Adds a server's API key from the keyring to a configuration dict."""
    import keyring

    p = keyring.get_password(conf[server]["host"], conf[server]["username"])
    conf[server]["api_key"] = p
    return conf
