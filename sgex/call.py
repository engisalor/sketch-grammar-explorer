"""API call classes."""
import hashlib
import json

import yaml


class Call:
    """Base class for API call types.

    Args:
        type: Name of API call as used in request URLS (e.g., `freqs`).
        params (dict): Call parameters.
        required: Minimum parameters needed for API requests to function.
    """

    @staticmethod
    def validate_params(
        params: dict, required: list, formats=["json", "xml", "csv", "txt"]
    ):
        """Checks whether a call meets minimum API parameter/formatting requirements.

        Args:
            params (dict): Call parameters.
            required: Minimum parameters needed for API requests to function.
            formats: Accepted data formats that can be retrieved.

        Raises:
            ValueError: A required parameter is missing.
        """
        params["format"] = params.get("format", "json")
        if params["format"] not in formats:
            raise ValueError(f'format must be one of {formats}: {params["format"]}')
        for p in required:
            if not params.get(p):
                raise ValueError(f"{p} parameter missing: {params}")

    @staticmethod
    def normalize_params(value):
        """Recursively normalizes values for a dictionary of parameters.

        Args:
            value: Generally a `dict` or `list` containing various items.

        Returns:
            A version of `value` that's more standardized for API requests: strips
            extra spaces, orders lists.
        """

        def _inner(value):
            if isinstance(value, str):
                value = value.strip()
            elif isinstance(value, list):
                value = [_inner(x) for x in value]
                value.sort()
            elif isinstance(value, dict):
                value = {k.strip(): _inner(v) for k, v in value.items()}
            else:
                pass
            return value

        return _inner(value)

    def to_json(self) -> str:
        """Converts call parameters to a JSON string."""
        dt = {
            (k): (str(v) if isinstance(v, (int, float)) else v)
            for k, v in self.params.items()
        }
        return json.dumps(dt, sort_keys=True)

    def to_hash(self) -> str:
        """Generates a hash of call parameters from an ordered JSON representation."""
        return hashlib.blake2b(self.to_json().encode()).hexdigest()[0:32]

    def to_yaml(self) -> str:
        """Converts call parameters to a YAML string."""
        dt = {
            (k): (str(v) if isinstance(v, (int, float)) else v)
            for k, v in self.params.items()
        }
        return yaml.dump(dt, sort_keys=True, default_flow_style=True).strip("\n")

    def __repr__(self) -> str:
        return f"{self.type.capitalize()} {self.to_hash()[:7]} {self.to_yaml()}"

    def __init__(self, type: str, params: dict, required: list = ["corpname"]):
        self.validate_params(params, required)
        self.params = self.normalize_params(params)
        self.required = set(required)
        self.type = type


class AttrVals(Call):
    """Gets an attribute's values.

    Args:
        params (dict): Call parameters.

    Hint:
        Requires `["corpname", "avattr"]`."""

    def __init__(self, params: dict):
        super().__init__("attr_vals", params, ["corpname", "avattr"])


class Collx(Call):
    """Gets a query's collocations.

    Args:
        params (dict): Call parameters.

    Hint:
        Requires `["corpname", "q"]`."""

    def __init__(self, params: dict):
        super().__init__("collx", params, ["corpname", "q"])


class CorpInfo(Call):
    """Gets information about a corpus.

    Args:
        params (dict): Call parameters.

    Hint:
        Requires `["corpname"]`."""

    def __init__(self, params: dict):
        super().__init__("corp_info", params, ["corpname"])


class ExtractKeywords(Call):
    """Gets corpus keywords in comparison to a reference corpus.

    Args:
        params (dict): Call parameters.

    Hint:
        Requires `["corpname", "ref_corpname"]`."""

    def __init__(self, params: dict):
        super().__init__("extract_keywords", params, ["corpname", "ref_corpname"])


class Freqs(Call):
    """Gets frequencies for a query (standard).

    Args:
        params (dict): Call parameters.

    Hint:
        Requires `["corpname", "q", "fcrit"]`."""

    def __init__(self, params: dict):
        super().__init__("freqs", params, ["corpname", "q", "fcrit"])


class Freqml(Call):
    """Gets frequencies for a query (ml).

    Args:
        params (dict): Call parameters.

    Hint:
        Requires `["corpname", "q", "fcrit"]`."""

    def __init__(self, params: dict):
        super().__init__("freqml", params, ["corpname", "q", "fcrit"])


class Freqtt(Call):
    """Gets frequencies for a query (tt).

    Args:
        params (dict): Call parameters.

    Hint:
        Requires `["corpname", "q", "fcrit"]`."""

    def __init__(self, params: dict):
        super().__init__("freqtt", params, ["corpname", "q", "fcrit"])


class Subcorp(Call):
    """Gets information about a corpus's subcorpora.

    Args:
        params (dict): Call parameters.

    Hint:
        Requires `["corpname"]`."""

    def __init__(self, params: dict):
        super().__init__("subcorp", params, ["corpname"])


class TextTypesWithNorms(Call):
    """Gets data on a corpus's text types.

    Args:
        params (dict): Call parameters.

    Hint:
        Requires `["corpname"]`."""

    def __init__(self, params: dict):
        super().__init__("texttypes_with_norms", params, ["corpname"])


class Thes(Call):
    """Gets thesaurus information.

    Args:
        params (dict): Call parameters.

    Hint:
        Requires `["corpname", "lemma"]`.

    Important:
        Not available in NoSketch Engine.
    """

    def __init__(self, params: dict):
        super().__init__("thes", params, ["corpname", "lemma"])


class View(Call):
    """Gets concordances for a query (defaults to `asyn=0`).

    Args:
        params (dict): Call parameters.

    Hint:
        Requires `["corpname", "q"]`.
    """

    def __init__(self, params: dict):
        if not params.get("asyn"):
            params["asyn"] = 0
        super().__init__("view", params, ["corpname", "q"])


class Wordlist(Call):
    """Get a list of words by frequency.

    Args:
        params (dict): Call parameters.

    Hint:
        Requires `["corpname", "wltype", "wlattr"]`."""

    def __init__(self, params: dict):
        super().__init__("wordlist", params, ["corpname", "wltype", "wlattr"])


class Wsdiff(Call):
    """Gets a comparison between two word sketches.

    Args:
        params (dict): Call parameters.

    Hint:
        Requires `["corpname", "lemma", "lemma2"]`.

    Important:
        Not available in NoSketch Engine.
    """

    def __init__(self, params: dict):
        super().__init__("wsdiff", params, ["corpname", "lemma", "lemma2"])


class Wsketch(Call):
    """Gets a word sketch.

    Args:
        params (dict): Call parameters.

    Hint:
        Requires `["corpname", "lemma"]`.

    Important:
        Not available in NoSketch Engine.
    """

    def __init__(self, params: dict):
        super().__init__("wsketch", params, ["corpname", "lemma"])
