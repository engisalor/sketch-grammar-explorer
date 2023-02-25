import pandas as pd
from requests import Response


def structures_json(
    response: Response, drop: list = ["attributes", "label", "dynamic", "fromattr"]
) -> pd.DataFrame:
    """Returns a DataFrame describing corpus structures and their attributes."""
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
    """Returns a DataFrame of corpus structure sizes (overall token/word counts)."""
    return pd.DataFrame(
        {
            "structure": [
                k.replace("count", "") for k in response.json().get("sizes").keys()
            ],
            "size": [int(v) for v in response.json().get("sizes").values()],
        }
    )
