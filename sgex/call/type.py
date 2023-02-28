"""Types of API calls and their classes."""
from sgex.config import formats

types = [
    "attr_vals",
    "collx",
    "corp_info",
    "extract_keywords",
    "freqml",
    "freqs",
    "freqtt",
    "subcorp",
    "thes",
    "view",
    "wordlist",
    "wsdiff",
    "wsketch",
]


class Call:
    """Base class for API calls with a generic method for call validation."""

    def validate(self):
        """Checks whether a call meets basic API parameter/formatting requirements."""
        if self.params.get("format"):
            if self.params["format"] not in formats:
                raise ValueError(f"format must be one of {formats}: {self.dt}")
        for p in self.required:
            if not self.params.get(p):
                raise ValueError(f"{p} missing: {self.dt}")

    def __repr__(self) -> str:
        if not self.key:
            key = "*"
        else:
            key = self.key[:8]
        return f"{self.type.upper()}({key}) {self.params}"

    def __init__(self, type: str, params: dict, required: list = ["corpname"]):
        self.type = type
        self.params = params
        if self.type not in types:
            raise ValueError(f"type must be one of {types}")
        if not isinstance(self.params, dict):
            raise TypeError("params must be a dict")
        self.required = set(required)
        self.key = None
        self.dt = {"type": self.type, **self.params}


class AttrVals(Call):
    """Gets an attribute's values."""

    def __init__(self, params: dict):
        super().__init__("attr_vals", params, ["corpname", "avattr"])


class Collx(Call):
    """Gets a query's collocations."""

    def __init__(self, params: dict):
        super().__init__("collx", params, ["corpname", "q"])


class CorpInfo(Call):
    """Gets information about a corpus."""

    def __init__(self, params: dict):
        super().__init__("corp_info", params, ["corpname"])


class ExtractKeywords(Call):
    """Gets corpus keywords in comparison to a reference corpus."""

    def __init__(self, params: dict):
        super().__init__("extract_keywords", params, ["corpname", "ref_corpname"])


class Freqs(Call):
    """Gets frequencies for a query (standard)."""

    def __init__(self, params: dict):
        super().__init__("freqs", params, ["corpname", "q", "fcrit"])


class Freqml(Call):
    """Gets frequencies for a query (ml)."""

    def __init__(self, params: dict):
        super().__init__("freqml", params, ["corpname", "q", "fcrit"])


class Freqtt(Call):
    """Gets frequencies for a query (tt). TODO not tested"""

    def __init__(self, params: dict):
        super().__init__("freqtt", params, ["corpname", "q", "fcrit"])


class Subcorp(Call):
    """Gets information about a corpus's subcorpora."""

    def __init__(self, params: dict):
        super().__init__("subcorp", params, ["corpname"])


class Thes(Call):
    """Gets thesaurus information (full Sketch Engine only)."""

    def __init__(self, params: dict):
        super().__init__("thes", params, ["corpname", "lemma"])


class View(Call):
    """Gets concordances for a query (defaults to ``asyn=0``)."""

    def __init__(self, params: dict):
        if not params.get("asyn"):
            params["asyn"] = 0
        super().__init__("view", params, ["corpname", "q"])


class Wordlist(Call):
    """Get a list of words by frequency."""

    def __init__(self, params: dict):
        super().__init__("wordlist", params, ["corpname", "wltype", "wlattr"])


class Wsdiff(Call):
    """Gets a comparison between two word sketches (full Sketch Engine only)."""

    def __init__(self, params: dict):
        super().__init__("wsdiff", params, ["corpname", "lemma", "lemma2"])


class Wsketch(Call):
    """Gets a word sketch (full Sketch Engine only)."""

    def __init__(self, params: dict):
        super().__init__("wsketch", params, ["corpname", "lemma"])
