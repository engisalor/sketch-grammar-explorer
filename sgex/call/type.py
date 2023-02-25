"""Types of API calls and their classes."""
from sgex.call.call import formats

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
        return f"{self.type.upper()}({self.key[:8]}*) {self.params}"

    def __init__(self, type: str, params: dict, required: list = ["corpname"]):
        self.type = type
        self.params = params
        self.required = set(required)
        self.dt = {"type": self.type, **self.params}
        if self.type not in types:
            raise ValueError(f"type must be one of {types}")
        if not isinstance(self.params, dict):
            raise TypeError("params must be a dict")


class AttrVals(Call):
    def __init__(self, params: dict):
        super().__init__("attr_vals", params, ["corpname", "avattr"])


class Collx(Call):
    def __init__(self, params: dict):
        super().__init__("collx", params, ["corpname", "q"])


class CorpInfo(Call):
    def __init__(self, params: dict):
        super().__init__("corp_info", params, ["corpname"])


class ExtractKeywords(Call):
    def __init__(self, params: dict):
        super().__init__("extract_keywords", params, ["corpname"])


class Freqs(Call):
    def __init__(self, params: dict):
        super().__init__("freqs", params, ["corpname", "q", "fcrit"])


class Freqml(Call):
    def __init__(self, params: dict):
        super().__init__("freqml", params, ["corpname", "q", "fcrit"])


class Freqtt(Call):
    def __init__(self, params: dict):
        super().__init__("freqtt", params, ["corpname", "q", "fcrit"])


class Subcorp(Call):
    def __init__(self, params: dict):
        super().__init__("subcorp", params, ["corpname"])


class Thes(Call):
    def __init__(self, params: dict):
        super().__init__("thes", params, ["corpname", "lemma"])


class Wordlist(Call):
    def __init__(self, params: dict):
        super().__init__("wordlist", params, ["corpname", "wltype", "wlattr"])


class Wsdiff(Call):
    def __init__(self, params: dict):
        super().__init__("wsdiff", params, ["corpname", "lemma", "lemma2"])


class Wsketch(Call):
    def __init__(self, params: dict):
        super().__init__("wsketch", params, ["corpname", "lemma"])


class View(Call):
    def __init__(self, params: dict):
        if not params.get("asyn"):
            params["asyn"] = 0
        super().__init__("view", params, ["corpname", "q"])
