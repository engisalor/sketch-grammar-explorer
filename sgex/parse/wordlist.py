import pandas as pd
from requests import Response


def ttype_analysis_json(response: Response) -> pd.DataFrame:
    """Returns a DataFrame with attribute frequencies, e.g., to analyze text types.

    Args:
        response: Response object.

    Example:
        This example gets a DataFrame with ``doc.file`` values.

        >>> call= Wordlist({
            "corpname": "susanne",
            "wlattr": "doc.file",
            "wltype": "simple",
            "wlminfreq": 1,
            })
        >>> p = Package(call, "noske", default)
        >>> p.send_requests()
        >>> wordlist.ttype_analysis_json(p.responses[0])
            str  frq  relfreq attribute
        0   A19   12    79.77  doc.file
        1   A10    9    59.83  doc.file
        2   A02    8    53.18  doc.file
        ...
    """
    json = response.json()
    df = pd.DataFrame.from_records(json.get("Items"))
    df["attribute"] = json.get("request").get("wlattr")
    df = df.round(2)
    df.sort_values("frq", ascending=False, inplace=True)
    return df
