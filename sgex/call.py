# Copyright (c) 2022-2023 Loryn Isaacs
# This file is part of Sketch Grammar Explorer, licensed under BSD-3
# See the LICENSE file at https://github.com/engisalor/sketch-grammar-explorer/
"""API call classes."""
import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

import aiofiles
import aiohttp
import pandas as pd
import yaml
from multidict import MultiDict
from yarl import URL

from sgex import util


@dataclass
class CachedResponse:
    """A mock Response class for managing caching.

    Args:
        file_meta: Where call metadata is saved.
        file_text: Where call text data is saved.

    Methods:
        set: Saves newly requested data.
        get: Loads cached data.

    Attributes:
        url: yarl URL for the call.
        status: Response status.
        reason: Response reason.
        headers: Response headers.
        ske_error: Detected SkE server error (e.g. for a malformed CQL rule).
        text: Response text.
    """

    file_meta: Path
    file_text: Path
    url: URL = field(default_factory=URL)
    status: int = field(default_factory=int)
    reason: str = field(default_factory=str)
    headers: dict = field(default_factory=dict)
    ske_error: str = field(default_factory=str)
    text: str = field(default_factory=str)

    @staticmethod
    def redact_json(dt: dict) -> str:
        """Removes API credentials from a dict."""
        if dt.get("request"):
            _ = dt["request"].pop("api_key", None)
            _ = dt["request"].pop("username", None)
        return dt

    @staticmethod
    def redact_url(url: URL) -> URL:
        """Removes API credentials from a yarl url."""
        dt = MultiDict(url.query)
        _ = dt.popall("api_key", None)
        _ = dt.popall("username", None)
        return url.with_query(dt)

    async def set(self, response: aiohttp.ClientResponse):
        """Parses a Response and saves to cache."""
        self.url = str(self.redact_url(response.url))
        self.status = response.status
        self.reason = response.reason
        self.headers = dict(response.headers)
        if "application/json" in response.headers.get("Content-Type"):
            j = await response.json()
            self.ske_error = j.get("error", "")
            self.text = json.dumps(self.redact_json(j), indent=2, ensure_ascii=False)
        else:
            self.ske_error = "unimplemented"
            self.text = await response.text()
            self.text = self.text.lstrip("\ufeff")
        if self.ske_error in ["", "unimplemented"]:
            async with aiofiles.open(self.file_meta, "w") as f:
                await f.write(
                    json.dumps(
                        {
                            "url": self.url,
                            "status": self.status,
                            "reason": self.reason,
                            "headers": self.headers,
                            "ske_error": self.ske_error,
                        },
                        indent=2,
                        ensure_ascii=False,
                    )
                )
            async with aiofiles.open(self.file_text, "w") as f:
                await f.write(self.text)

    def get(self):
        """Retrieves a cached response."""
        if self.file_meta.exists() and self.file_text.exists():
            dt = util.read_json(self.file_meta)
            with open(self.file_text) as f:
                dt |= {"text": f.read()}
            for k, v in dt.items():
                setattr(self, k, v)

    def json(self):
        """Returns a JSON object if this content type is available."""
        content_type = self.headers.get("Content-Type")
        if "application/json" in content_type:
            return json.loads(self.text)
        else:
            raise ValueError(f"usable with `json` data only, not `{content_type}`")

    def hash(self) -> str:
        """Generates a hash of `response.request` w/ an ordered JSON representation."""
        dt = {
            (k): (str(v) if isinstance(v, (int, float)) else v)
            for k, v in self.response["request"].items()
        }
        _json = json.dumps(dt, sort_keys=True, ensure_ascii=False)
        return hashlib.blake2b(_json.encode()).hexdigest()[0:32]

    def __repr__(self) -> str:
        attrs = "<class 'sgex.call.CachedResponse'>\n"
        for k, v in self.__dict__.items():
            if k != "text":
                attrs += f"{(k)}    {str(v)[:min(len(str(v)), 80)]}\n"
            if k == "text":
                attrs += f"{(k)}    <{len(v.encode())} bytes>"
        return attrs


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

    def json(self) -> str:
        """Converts call parameters to a JSON string."""
        dt = {
            (k): (str(v) if isinstance(v, (int, float)) else v)
            for k, v in self.params.items()
        }
        return json.dumps(dt, sort_keys=True, ensure_ascii=False)

    def hash(self) -> str:
        """Generates a hash of call parameters w/ an ordered JSON representation."""
        return hashlib.blake2b(self.json().encode()).hexdigest()[0:32]

    def yaml(self) -> str:
        """Converts call parameters to a YAML string."""
        dt = {
            (k): (str(v) if isinstance(v, (int, float)) else v)
            for k, v in self.params.items()
        }
        return yaml.dump(
            dt, sort_keys=True, default_flow_style=True, allow_unicode=True
        ).strip("\n")

    def check_format(self, required_format: str = "json") -> None:
        if self.params["format"] != required_format:
            raise ValueError(
                f'usable with `json` data only, not `{self.params["format"]}`'
            )

    def __repr__(self) -> str:
        return f"{self.type.capitalize()} {self.hash()[:7]} {self.yaml()}"

    def __init__(
        self,
        type: str,
        params: dict,
        required: list = ["corpname"],
        response: CachedResponse = None,
    ):
        self.validate_params(params, required)
        self.params = self.normalize_params(params)
        self.required = set(required)
        self.type = type
        self.response = response


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

    def structures_from_json(
        self, drop: list = ["attributes", "label", "dynamic", "fromattr"]
    ) -> pd.DataFrame:
        """Returns a DataFrame of corpus structures and their attributes (text types).

        Args:
            drop: Unwanted columns.
        """
        self.check_format()
        if not self.params.get("struct_attr_stats", None) == 1:
            raise ValueError("requires `struct_attr_stats=1` to be set in params")
        df = pd.DataFrame()
        for s in self.response.json().get("structures"):
            temp = pd.DataFrame.from_records(s)
            if not temp.empty:
                temp.drop(["size", "label"], axis=1, inplace=True)
                temp.rename({"name": "structure"}, axis=1, inplace=True)
                temp = pd.concat([temp, pd.json_normalize(temp["attributes"])], axis=1)
                temp.drop(drop, axis=1, inplace=True)
                temp.rename({"name": "attribute"}, axis=1, inplace=True)
                df = pd.concat([df, temp])
        return df

    def sizes_from_json(self) -> pd.DataFrame:
        """Returns a DataFrame of corpus structure sizes (token/word counts)."""
        self.check_format()
        _json = self.response.json()
        return pd.DataFrame(
            {
                "structure": [
                    k.replace("count", "") for k in _json.get("sizes").keys()
                ],
                "size": [int(v) for v in _json.get("sizes").values()],
            }
        )

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

    @staticmethod
    def _clean_items(items, item_keys=["Word", "frq", "rel", "fpm", "reltt"]) -> list:
        """Extracts desired items from block and flattens ``Word`` values."""
        clean = []
        for block in items:
            b = []
            for i in block:
                dt = {k: v for k, v in i.items() if k in item_keys}
                words = util.flatten_ls_of_dt(dt["Word"])
                dt["value"] = "|".join(words["n"])
                del dt["Word"]
                b.append(dt)
            clean.append(b)
        return clean

    @staticmethod
    def _clean_heads(heads) -> list:
        """Extracts each block's fcrit attribute: ``head[0]["id"]``."""
        if len([x for x in heads if x]):
            return [head[0].get("id") for head in heads]
        else:
            return None

    def df_from_json(self) -> pd.DataFrame:
        """Converts a single-/multi-block freqs JSON response to a DataFrame.

        TODO:
            fix: This use of `Desc` assumes a simple call w/o filters etc.
            docs: "rel" in "Desc" refers to a query's fpm in the whole corpus
                as shown in the user interface.
        """
        self.check_format()
        _json = self.response.json()
        blocks = _json.get("Blocks", [])
        heads = self._clean_heads([block.get("Head") for block in blocks])
        if not heads:
            return pd.DataFrame()
        else:
            items = self._clean_items([block.get("Items") for block in blocks])
            # combine extracted data
            for b in range(len(blocks)):
                for i in range(len(items[b])):
                    items[b][i]["attribute"] = heads[b]
            # convert to DataFrame
            df = pd.DataFrame.from_records([x for y in items for x in y])
            # get specific values
            df["arg"] = _json.get("Desc", [])[0].get("arg", None)
            df["nicearg"] = _json.get("Desc", [])[0].get("nicearg", None)
            df["corpname"] = _json.get("request", {}).get("corpname", None)
            #
            df["total_fpm"] = _json.get("Desc", [])[0].get("rel", None)
            df["total_frq"] = _json.get("Desc", [])[0].get("size", None)
            df["fmaxitems"] = _json.get("request", {}).get("fmaxitems", None)
            return df

    def __init__(self, params: dict):
        super().__init__("freqs", params, ["corpname", "q", "fcrit"])


class Freqml(Freqs):
    """Gets frequencies for a query (ml).

    Args:
        params (dict): Call parameters.

    Hint:
        Requires `["corpname", "q", "fcrit"]`."""

    def __init__(self, params: dict):
        super().__init__("freqml", params, ["corpname", "q", "fcrit"])


class Freqtt(Freqs):
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

    def text_types_from_json(
        self, drops: tuple = ("doc.wordcount",), position: str = ""
    ) -> list:
        """Returns corpus text types.

        Args:
            drops: Corpus structures to exclude from returned list.
            position: fcrit position (see SkE docs for `view` and `fcrit` syntax).

        Notes:
            - `drops` uses a `startswith` string method; excluding a class of
                structures can be accomplished with, e.g., `drops=("doc.",)`.
            - `position` can be used for generating ready-to-use fcrit lists.
        """
        self.check_format()
        _json = self.response.json()
        blocks = [x for x in _json.get("Blocks")]
        ttypes = [x["Line"][0]["name"] for x in blocks]
        if drops:
            out = [x for x in ttypes if not x.startswith(drops)]
        if position:
            out = [f"{x} {position}" for x in ttypes]
        return out

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
        Requires `["corpname"]` and either `"q"` or `"json"`.
    """

    @staticmethod
    def _line_to_tacred(line: dict) -> dict:
        """Builds a dictionary of lists of tokens, tags, etc., from a View call line.

        Args:
            line: an item in response `Lines`. See note about required parameters.

        Note:
            Requires View data with `attrs="word,tag,lemma", attr_allpos="all"`.
        """
        line_attrs = []
        line_strs = []
        for section in ["Left", "Kwic", "Right"]:
            line_attrs.extend([x["str"] for x in line[section] if x["class"] == "attr"])
            line_strs.extend([x["str"] for x in line[section] if x["class"] != "attr"])
            line_pos = []
            line_lemma = []
            for e in line_attrs:
                attrs_split = re.findall("/([^/]+)/(.+)", e)
                if len(attrs_split) != 1 or len(attrs_split[0]) != 2:
                    raise ValueError(f"can't split pos & lemma in {e}")
                pos = "".join([i for i in attrs_split[0][0] if not i.isdigit()])
                line_pos.append(pos)
                line_lemma.append(attrs_split[0][1])
            token = {str(x): line_strs[x].strip() for x in range(len(line_strs))}
            pos = {str(x): line_pos[x].strip() for x in range(len(line_pos))}
            lemma = {str(x): line_lemma[x].strip() for x in range(len(line_lemma))}
        return {
            "toknum": line["toknum"],
            "token": token,
            "pos": pos,
            "lemma": lemma,
        }

    def lines_to_tacred(self) -> list:
        """Returns a list of lines converted to annotation dicts from a View call.

        Note:
            Requires View data with `attrs="word,tag,lemma"`, `attr_allpos="all"` and
            `"refs": "<desired structures>"`.

            Returns a JSON structure for sentence annotation that approximates the
            TACRED dataset format: https://doi.org/10.35111/m0kp-4w25.
        """
        items = []
        _json = self.response.json()
        for line in _json["Lines"]:
            new = self._line_to_tacred(line)
            new["corpus"] = _json["request"]["corpname"]
            new["refs"] = line["Refs"]
            new["desc"] = _json["Desc"]
            items.append(new)
        return items

    def ttypes_to_df(self, ttypes: list) -> pd.DataFrame:
        """Returns a DataFrame with token number and text types for each concordance.

        Args:
            ttypes: A list of text types (corpus attributes) to analyze. Must correspond
                with the `refs` View call parameter (see example).

        Notes:
            - Requires a View call with `refs` (see example for a proper comma-separated
                string). `refs` must start with `#` (retrieves `toknum`) and each text
                type should be prepended with `=` to return the value w/o its label.
            - Use `Job.run_repeat()` to get all View concordances, otherwise results are
                limited to the first page (`fromp=1`). See `Job.run_repeat()` docstring.
            - Set View parameters `kwicleftctx` and `kwicrightctx` to `0` to minimize
                download size (if the concordance itself can be discarded).

        Example:
            ```py
            >>> from sgex.job import Job

            # corpus text types (only include pertinent ones)
            >>> ttypes_susanne = ["doc.file", "doc.n"]

            # view call params
            >>> params={
            ... "call_type": "View",
            ... "corpname": "susanne",
            ... "q": 'aword,"work"',
            ... "refs": "#," + ",".join(["=" + x for x in ttypes_susanne]),
            ... "kwicleftctx": 0,
            ... "kwicrightctx": 0,
            ... "pagesize": 10}
            ...

            # run job (local noske server with Susanne corpus loaded)
            >>> j = Job(params=params)
            >>> j.run_repeat()

            # make DF for one call (each DF is one page)
            >>> df = j.data.view[0].ttypes_to_df(ttypes_susanne)
            >>> len(df) == params["pagesize"]
            True

            # make DF for all calls
            >>> dfs = [j.data.view[x].ttypes_to_df(ttypes_susanne)
            ... for x in range(len(j.data.view))]
            >>> df = pd.concat(dfs)
            >>> len(df) == j.data.view[0].response.json()["concsize"]
            True

            # then use pd.value_counts() for frequency analysis
            # for all text types (exclude token number)
            >>> res = df.value_counts(list(df.columns)[1:])

            # for one text type
            >>> res = df.value_counts(["doc.file"])

            # for specific text types matching a value
            >>> res = df.query('`doc.file` == "A10"').value_counts(ttypes_susanne)

            # tip: use df.value_counts([<columns>]).reset_index() to return a DF
            ```
        """
        self.check_format()
        _json = self.response.json()
        data = [x["Refs"] for x in _json["Lines"]]
        columns = ["#"] + ttypes
        df = pd.DataFrame(data, columns=columns)
        df["#"] = df["#"].str.replace("#", "")
        df["#"] = df["#"].astype(int)
        return df

    def __init__(self, params: dict):
        if not params.get("asyn"):
            params["asyn"] = 0
        super().__init__("view", params, ["corpname"])


class Wordlist(Call):
    """Get a list of words by frequency.

    Args:
        params (dict): Call parameters.

    Hint:
        Requires `["corpname", "wltype", "wlattr"]`."""

    def df_from_json(self) -> pd.DataFrame:
        """Returns a DataFrame with attribute frequencies.

        Notes:
            - Usable for text type analysis w/ `wltype=simple` and if a structure is
                supplied to `wlattr`, e.g., `doc.file`.
        """
        self.check_format()
        _json = self.response.json()
        df = pd.DataFrame.from_records(_json.get("Items"))
        df["attribute"] = _json.get("request").get("wlattr")
        df = df.round(2)
        df.sort_values("frq", ascending=False, inplace=True)
        return df

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


@dataclass
class Data:
    """Dataclass to store lists of calls by subclass.

    Attributes:
        One attribute for each of the `Call` types. E.g., `Data.view` accesses a list
        of stored concordance data.

    Methods:
        add: Appends new call data to the appropriate call type.
        list: Returns a list of all `Call` data.
        len: Returns the total number of stored calls.
        reset: Clears data for all call types.
    """

    attrvals: List[AttrVals] = field(default_factory=list)
    call: List[Call] = field(default_factory=list)
    collx: List[Collx] = field(default_factory=list)
    corpinfo: List[CorpInfo] = field(default_factory=list)
    extractkeywords: List[ExtractKeywords] = field(default_factory=list)
    freqml: List[Freqml] = field(default_factory=list)
    freqs: List[Freqs] = field(default_factory=list)
    freqtt: List[Freqtt] = field(default_factory=list)
    subcorp: List[Subcorp] = field(default_factory=list)
    texttypeswithnorms: List[TextTypesWithNorms] = field(default_factory=list)
    thes: List[Thes] = field(default_factory=list)
    view: List[View] = field(default_factory=list)
    wordlist: List[Wordlist] = field(default_factory=list)
    wsdiff: List[Wsdiff] = field(default_factory=list)
    wsketch: List[Wsketch] = field(default_factory=list)

    def add(self, call: Call | list[Call]):
        """Adds an object or list of objects of `Call` class or subclasses to `Data`.

        Args:
            call: An object of `Call` class or subclass or list of these.

        Notes:
            Sorts objects by type, storing them in an attribute of the same name
            (lowercase). E.g., `CorpInfo` calls are stored in `self.corpinfo`.

            This is the primary method for adding data, rather than instantiation.
        """
        if not isinstance(call, list):
            call = [call]
        for c in call:
            _type = type(c).__name__.lower()
            getattr(self, _type).append(c)

    def list(self) -> list[Call]:
        """Returns a flat list of all calls stored in `Data`."""
        return [y for x in self.__dict__.values() for y in x]

    def len(self):
        """Calculates the number of stored calls."""
        return len(self.list())

    def reset(self):
        """Clears list values for all call data."""
        self.attrvals = []
        self.call = []
        self.collx = []
        self.corpinfo = []
        self.extractkeywords = []
        self.freqs = []
        self.freqml = []
        self.freqtt = []
        self.subcorp = []
        self.texttypeswithnorms = []
        self.thes = []
        self.view = []
        self.wordlist = []
        self.wsdiff = []
        self.wsketch = []

    def __repr__(self) -> str:
        return "<class 'sgex.call.Data'>\n" + "\n".join(
            [
                f"{k} ({len(v)})    {v[:min(len(v), 3)]}"
                for k, v in self.__dict__.items()
                if v
            ]
        )
