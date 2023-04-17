"""Functions for assembling CQL rules from query strings."""
import re

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


def query_to_cql(query: str):
    """Converts a word/phrase into a ``lc`` and ``lemma_lc`` CQL rule."""
    words = [x for x in query.split() if x]
    return " ".join([f'[lc="{w.strip()}" | lemma_lc="{w.strip()}"]' for w in words])


def apart(query: str):
    """Separates hyphenated words with a space."""
    return query.replace("-", " ").replace("  ", " ")


def nospace(query: str):
    """Joins hyphenated words."""
    return query.replace("-", "")


def joined(query: str):
    """Replaces double hyphens with a single hyphen."""
    return query.replace("--", "-")


def atomic(query: str):
    """Separates hyphenated words and keeps the hyphen as a token."""
    return " ".join(re.split("(-)", query)).replace("-  -", "-")


def if_atomic(query: str, atomic_hyphens: bool):
    """Controls whether to apply ``atomic()`` to a query."""
    if atomic_hyphens:
        return atomic(query)
    else:
        return None


def query_to_dict(query: str, atomic_hyphens: bool = True):
    """Decomposes a query string into a dict of components, w or w/o atomic hyphens."""
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
                    nospace(q[y]),
                    apart(q[y]),
                    joined(q[y]),
                    if_atomic(q[y], atomic_hyphens),
                ]
            elif "-" in q[y]:
                queries[x][y] = [q[y], if_atomic(q[y], atomic_hyphens)]
            else:
                queries[x][y] = [q[y]]
            queries[x][y] = [a for a in queries[x][y] if a]
    return queries


def query_escape(query: str):
    """Escapes special CQL characters in a string.

    Note:
        Single backslashes are converted to four backslashes, which is needed to query
        this literal character in current CQL behavior. Querying a single backslash in
        SkE's simple query returns strings in angled brackets, not backslashes.
    """
    return "".join([escape_symbols.get(c, c) for c in query])


def simple_query(query: str, atomic_hyphens=True):
    """Converts a query string into a CQL rule following SkE ``simple`` behavior."""
    query = query_escape(query)
    queries = query_to_dict(query, atomic_hyphens)
    dt = queries.copy()
    all = []
    for v in dt.values():
        ls = []
        for c in v.keys():
            v[c] = [query_to_cql(phrase) for phrase in v[c]]
            if len(v[c]) > 1:
                v[c] = "( " + " | ".join(v[c]) + " )"
            else:
                v[c] = " | ".join(v[c])
            ls.append(v[c])
        all.append("".join(ls))
    cql = "q" + "|".join(all)
    cql = cql.replace("*", ".*").replace("?", ".")
    return cql
