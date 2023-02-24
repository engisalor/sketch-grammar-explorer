import pandas as pd
from requests import Response


def ttype_analysis(response: Response) -> pd.DataFrame:
    """Returns a DataFrame with attribute frequencies, e.g., to analyze text types."""
    json = response.json()
    df = pd.DataFrame.from_records(json.get("Items"))
    df["attribute"] = json.get("request").get("wlattr")
    df = df.round(2)
    df.sort_values("frq", ascending=False, inplace=True)
    return df
