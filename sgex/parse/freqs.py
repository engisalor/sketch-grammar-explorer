import pandas as pd
from requests import Response

from sgex.util import flatten_ls_of_dt


def clean_items(items, item_keys=["Word", "frq", "rel", "fpm", "reltt"]) -> list:
    """Extracts desired items from block and flattens ``Word`` values."""
    clean = []
    for block in items:
        b = []
        for i in block:
            dt = {k: v for k, v in i.items() if k in item_keys}
            words = flatten_ls_of_dt(dt["Word"])
            dt["value"] = "|".join(words["n"])
            del dt["Word"]
            b.append(dt)
        clean.append(b)
    return clean


def clean_heads(heads) -> list:
    """Extracts each block's fcrit attribute: ``head[0]["id"]``."""
    if len([x for x in heads if x]):
        return [head[0].get("id") for head in heads]
    else:
        return None


def freqs_json(response: Response) -> pd.DataFrame:
    """Converts a single-/multi-block freqs JSON response to a DataFrame.

    Args:
        response: Response object.

    Example:
        >>> call = Freqs({
            "corpname": "susanne", "q": 'alemma,"day"', "fcrit": "doc.file 0"
            })
        >>> p = Package(call, "noske", default)
        >>> p.send_requests()
        >>> df = freqs.freqs_json(p.responses[0])
        >>> df.iloc[0]
        frq                     8
        rel              426.2205
        reltt         3286.770748
        ...
    """
    json = response.json()
    # extract data from response
    blocks = json.get("Blocks", [])
    heads = clean_heads([block.get("Head") for block in blocks])
    if not heads:
        return pd.DataFrame()
    else:
        items = clean_items([block.get("Items") for block in blocks])
        # combine extracted data
        for b in range(len(blocks)):
            for i in range(len(items[b])):
                items[b][i]["attribute"] = heads[b]
        # convert to DataFrame
        df = pd.DataFrame.from_records([x for y in items for x in y])
        # get specific values
        df["arg"] = json.get("Desc", [])[0].get("arg", None)
        df["nicearg"] = json.get("Desc", [])[0].get("nicearg", None)
        df["corpname"] = json.get("request", {}).get("corpname", None)
        # NOTE API uses "rel" in "Desc" to refer to a query's
        # fpm in the whole corpus as shown in the user interface
        df["total_fpm"] = json.get("Desc", [])[0].get("rel", None)
        df["total_frq"] = json.get("Desc", [])[0].get("size", None)
        df["fmaxitems"] = json.get("request", {}).get("fmaxitems", None)
        return df
