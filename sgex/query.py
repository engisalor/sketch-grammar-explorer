# Copyright (c) 2022-2023 Loryn Isaacs
# This file is part of Sketch Grammar Explorer, licensed under BSD-3
# See the LICENSE file at https://github.com/engisalor/sketch-grammar-explorer/
"""Functions for assembling CQL rules from strings."""
import re
from collections import OrderedDict
from dataclasses import dataclass
from itertools import groupby
from unicodedata import normalize

# characters normalized to `'`
single_quotes = "‘’‛‹›"
# characters normalized to `"`
double_quotes = "ʺ˝ˮ˵˶̋«»“”‟"
# mapping to replace special characters in CQL rules
escape_symbols = {
    '"': r'\\"',
    "$": r"\$",
    "(": r"\(",
    ")": r"\)",
    "+": r"\+",
    "[": r"\[",
    "]": r"\]",
    "^": r"\^",
    "{": r"\{",
    "}": r"\}",
    "\\": "\\\\\\\\",
}
# characters used to determine how tokens are split if a word starts/ends with one
token_punctuation = '!"#$%&()*+,-./:;<=>?@[\\]^_`{|}~'  # nosec


@dataclass
class TokenOverride:
    r"""Dataclass for mappings (`OrderedDict`) used for overriding tokenization.

    Notes:
        Mappings should generally be for a specific language or corpus tagset.
        Keys are strings (`"cannot"`) and values either a replacement (`"can not"`) or
        wildcards (`" []{,2} "`, w/ surrounding spaces).

        Dictionary order matters: place longer keys (`"abc"`) before potential
        substrings (`"ab"`). Requires regex escaping for periods, question marks, etc.
        (`e\.g\.`, not `e.g.`).
    """

    en = OrderedDict(
        {
            "cannot": " []{,2} ",
            r" e\.g\.": " []{,4} ",
            r" i\.e\.": " []{,4} ",
            r"\.\.\.": " []{,3} ",
            r" et al\.": " []{,3} ",
            r"Dr\.": " []{,2} ",
            r"Mr\.": " []{,2} ",
            r"Ms\.": " []{,2} ",
            r"Mrs\.": " []{,2} ",
            r" vs\.": " []{,2} ",
            r" [pP]\.": " []{,2} ",
            r"St\.": " []{,2} ",
            r" etc\.": " []{,2} ",
        }
    )


def _query_to_cql(query: str):
    """Converts a word/phrase into a `lc` and `lemma_lc` CQL rule."""
    words = [x for x in query.split() if x]
    return " ".join([f'[lc="{w.strip()}" | lemma_lc="{w.strip()}"]' for w in words])


def _apart(query: str):
    """Separates hyphenated words with a space."""
    return query.replace("-", " ").replace("  ", " ")


def _nospace(query: str):
    """Joins hyphenated words."""
    return query.replace("-", "")


def _joined(query: str):
    """Replaces double hyphens with a single hyphen."""
    return query.replace("--", "-")


def _atomic(query: str):
    """Separates hyphenated words and keeps the hyphen as a token."""
    return " ".join(re.split("(-)", query)).replace("-  -", "-")


def _if_atomic(query: str, atomic_hyphens: bool):
    """Controls whether to apply `atomic()` to a query."""
    if atomic_hyphens:
        return _atomic(query)
    else:
        return None


def _query_to_dict(query: str, atomic_hyphens: bool = True):
    """Decomposes a string into a dict of components, w/ or w/o atomic hyphens."""
    query = query.strip().split("|")
    queries = {}
    for x in range(len((query))):
        q = query[x].strip()
        queries[x] = {}
        q = query[x].split()
        for y in range(len(q)):
            queries[x][y] = []
            if "--" in q[y]:
                queries[x][y] = [
                    _nospace(q[y]),
                    _apart(q[y]),
                    _joined(q[y]),
                    _if_atomic(q[y], atomic_hyphens),
                ]
            elif "-" in q[y]:
                queries[x][y] = [q[y], _if_atomic(q[y], atomic_hyphens)]
            else:
                queries[x][y] = [q[y]]
            queries[x][y] = [a for a in queries[x][y] if a]
    return queries


def _query_escape(query: str):
    """Escapes special CQL characters in a string.

    Note:
        Single backslashes are converted to four backslashes, which is needed to query
        this literal character in current CQL behavior. Querying a single backslash in
        SkE's simple query returns strings in angled brackets, not backslashes.
    """
    return "".join([escape_symbols.get(c, c) for c in query])


def simple_query(query: str, atomic_hyphens: bool = True, clean: bool = True) -> str:
    """Converts a query string into a CQL rule following SkE `simple` behavior.

    Args:
        query: Corpus query.
        atomic_hyphens: Whether hyphens should be treated flexibly.
        clean: Whether `_clean_query` should be run on the query.

    Returns:
        A string formatted as an API query value, as in `q( [<CQL rules>] )`.

    Example:
        >>> simple_query("re-do")
        '( [lc="re-do" | lemma_lc="re-do"] | \
[lc="re" | lemma_lc="re"] \
[lc="-" | lemma_lc="-"] \
[lc="do" | lemma_lc="do"] )'
    """
    if clean:
        query = _clean_query(query)
    query = _query_escape(query)
    queries = _query_to_dict(query, atomic_hyphens)
    dt = queries.copy()
    all = []
    for v in dt.values():
        ls = []
        for c in v.keys():
            v[c] = [_query_to_cql(phrase) for phrase in v[c]]
            if len(v[c]) > 1:
                v[c] = "( " + " | ".join(v[c]) + " ) "
            else:
                v[c] = " | ".join(v[c])
            ls.append(v[c])
        all.append("".join(ls))
    cql = "|".join(all).strip()
    cql = cql.replace("*", ".*").replace("?", ".")
    return cql


def _clean_query(
    query: str,
    form: str = "NFKC",
    single_quote: str = single_quotes,
    double_quote: str = double_quotes,
) -> str:
    """Normalizes a string & standardizes whitespace, single/double quotes.

    Args:
        query: Corpus query.
        form: Value for `unicodedata.normalize`.
        single_quote: Characters interpreted as single quotes.
        double_quote: Characters interpreted as double quotes.
    """
    query = query.strip()
    query = re.sub(pattern=r"\s", repl=" ", string=query)
    query = re.sub(pattern=f"[{single_quote}]", repl="'", string=query)
    query = re.sub(pattern=f"[{double_quote}]", repl='"', string=query)
    query = normalize(form, query)
    return query


def fuzzy_query(
    context: str,
    clean: bool = True,
    override: OrderedDict = TokenOverride.en,
    max_length: int = 25,
    url_wildcards: int = 2,
) -> str:
    """Makes a fuzzy query from a sentence, replacing punctuation, etc. w/ wildcards.

    Args:
        context: A sentence or phrase that's long enough to warrant fuzzy searching.
        clean: Whether to apply `_clean_query` to the context.
        override: Mapping for overriding tokenization (see `TokenOverride` dataclass).
        max_length: Final number of tokens to include, if a context is quite long.
        url_wildcards: Number of wildcards desired to replace URLs, emails, etc. This
            depends on how a corpus is tokenized: URLs are usually one token, but they
            often get split erroneously. This sets a default number of wildcards to use
            to give more flexibility when dealing with URLs.

    Notes:
        Intended for re-locating concordances that were previously found and extracted
        from a corpus (or to find repeats in/across one or more corpora). May not work
        well with complicated sentences with URLs, numbers, symbols, or languages that
        depart from EN alphanumeric strings. See `TokenOverride` to customize behavior.

        Attempts to simplify URLs, email addresses, hyphenation, contractions, numbers
        and punctuation. The returned string is a CQL query formatted for a `word` or
        `word (lowercase)` search.

    Example:
        >>> fuzzy_query("Before yesterday, it was fine, don't you think?")
        '"Before" "yesterday" []{,1} "it" "was" "fine" []{,3} "you" "think"'
        >>> fuzzy_query("We saw 1,000.99% more visitors at www.example.com yesterday")
        '"We" "saw" []{,6} "more" "visitors" "at" []{,2} "yesterday"'
    """
    # string modifications
    if clean:
        context = _clean_query(context)
    if override:
        for k, v in override.items():
            context = re.sub(k, v, context)
    # tokenization
    ls = []
    for x in context.split():
        digits = re.findall(r"\d+", x)
        if len(x) > 1:
            if x.startswith("[]{,"):
                ls.extend([None] * int(digits[-1]))
            elif re.compile(r"((http|https|www|\S+@\S+)[\:\.])").match(x):
                ls.extend([None] * url_wildcards)
            elif "-" in x:
                ls.extend([None] * len(re.split("(-)", x)))
            elif "'" in x:
                ls.extend([None] * len(re.split("'", x)))
            elif x.isalnum():
                ls.append(x)
            elif x[0] in token_punctuation:
                if x[-1] in token_punctuation and x[1:-1].isalnum():
                    ls.extend([None, x[1:-1], None])
                elif x[1:].isalnum():
                    ls.extend([None, x[1:]])
                elif re.compile(r"^.?[,.\d]+.?$").match(x):
                    ls.extend([None] * len([y for y in re.split(r"(\d+)", x) if y]))
                else:
                    ls.append(None)
            elif x[-1] in token_punctuation and x[:-1].isalnum():
                ls.extend([x[:-1], None])
            elif re.compile(r"^.?[,.\d]+.?$").match(x):
                ls.extend([None] * len([x for x in re.split(r"(\d+)", x) if x]))
            else:
                ls.append(None)
        else:
            if x.isalnum():
                ls.append(x)
            else:
                ls.append(None)
    # cql rule
    groups = [
        [f'"{y}"' for y in g] if k else [y for y in g]
        for k, g in groupby(ls, key=lambda x: x is not None)
    ]
    tokens = []
    for x in groups:
        wildcards = 0
        for y in x:
            if y:
                tokens.append(y)
            else:
                wildcards += 1
        if wildcards:
            tokens.append(f"[]{{,{wildcards}}}")
    # ignore trailing/leading wildcards
    if len(tokens) > 1:
        for x in [0, -1]:
            if tokens[x].startswith("[]"):
                tokens.pop(x)
    return " ".join(tokens[: min(max_length, len(tokens))])
