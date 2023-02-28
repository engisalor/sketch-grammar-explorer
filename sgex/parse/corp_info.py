import pandas as pd
from requests import Response


def structures_json(
    response: Response, drop: list = ["attributes", "label", "dynamic", "fromattr"]
) -> pd.DataFrame:
    """Returns a DataFrame of corpus structures and their attributes.

    Args:
        response: Response object.
        drop: Unwanted columns.

    Example:
        >>> call= CorpInfo({"corpname": "susanne", "struct_attr_stats": 1})
        >>> p = Package(call, "noske", default)
        >>> p.send_requests()
        >>> corp_info.structures_json(p.responses[0])
            structure  attribute  size
        0      font       type     2
        0      head       type     2
        0       doc       file    64
        1       doc          n    12
        2       doc  wordcount     1
    """
    df = pd.DataFrame()
    for s in response.json().get("structures"):
        temp = pd.DataFrame.from_records(s)
        if not temp.empty:
            temp.drop(["size", "label"], axis=1, inplace=True)
            temp.rename({"name": "structure"}, axis=1, inplace=True)
            temp = pd.concat([temp, pd.json_normalize(temp["attributes"])], axis=1)
            temp.drop(drop, axis=1, inplace=True)
            temp.rename({"name": "attribute"}, axis=1, inplace=True)
            df = pd.concat([df, temp])
    return df


def sizes_json(response: Response) -> pd.DataFrame:
    """Returns a DataFrame of corpus structure sizes (token/word counts).

    Args:
        response: Response object.

    Example:
        >>> call = CorpInfo({"corpname": "susanne", "struct_attr_stats": 1})
        >>> p = Package(call, "noske", default)
        >>> p.send_requests()
        >>> corp_info.sizes_json(p.responses[0])
            structure    size
        0     token  150426
        1      word  128998
        2       doc     149
        3       par    1923
        4      sent       0
    """
    return pd.DataFrame(
        {
            "structure": [
                k.replace("count", "") for k in response.json().get("sizes").keys()
            ],
            "size": [int(v) for v in response.json().get("sizes").values()],
        }
    )
