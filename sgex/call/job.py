"""Classes to execute specific API jobs."""
import pandas as pd

from sgex.call.package import Package
from sgex.call.query import simple_query
from sgex.call.type import CorpInfo, Freqs, Wordlist
from sgex.config import default
from sgex.parse import corp_info, freqs, wordlist


class TTypeAnalysis:
    """Collects frequency data about a corpus's text types (attributes).

    Args:
        corpname: Corpus.
        server: Server.
        config: Configuration dict.

    Methods:
        get_corp_info: Makes a preliminary corp_info call.
        get_ttypes: Runs Wordlist calls for each attribute.
        make_df: Makes a DataFrame of results.
        run: Executes job.

    Notes:
        Default gets up to 500 attributes: ``"wlmaxitems": 500``

    Example:
        >>> j = job.TTypeAnalysis("susanne", "noske", default)
        >>> j.run()
        >>> j.df
                   str  frq  relfreq      attribute
        0         ital  263  1748.37      font.type
        1         bold   38   252.62      font.type
        2          maj  182  1209.90      head.type
        ...
    """

    def get_corp_info(self):
        """Makes a corp_info call to retrieve corpus structures as part of a job."""
        self.corpinfo_call = CorpInfo(self.corp_info_params)
        self.corpinfo_package = Package(self.corpinfo_call, self.server, self.config)
        self.corpinfo_package.send_requests()
        self.structures_df = corp_info.structures_json(
            self.corpinfo_package.responses[0]
        )
        self.attributes = (
            self.structures_df["structure"] + "." + self.structures_df["attribute"]
        )

    def get_ttypes(self):
        """Makes a series of wordlist calls to retrieve text type data."""
        self.ttype_calls = []
        for attr in self.attributes:
            params = {**self.wordlist_params, "wlattr": attr}
            self.ttype_calls.append(Wordlist(params))
        self.ttype_package = Package(self.ttype_calls, self.server, self.config)
        self.ttype_package.send_requests()

    def make_df(self):
        """Generates a DataFrame with combined text type data."""
        self.df = pd.DataFrame()
        for response in self.ttype_package.responses:
            temp = wordlist.ttype_analysis_json(response)
            self.df = pd.concat([self.df, temp])
        self.df.reset_index(drop=True, inplace=True)

    def run(self):
        """Executes the job."""
        self.get_corp_info()
        self.get_ttypes()
        self.make_df()

    def __init__(self, corpname: str, server: str, config: dict = default) -> None:
        self.corpname = corpname
        self.server = server
        self.config = config
        self.corp_info_params = {
            "corpname": corpname,
            "struct_attr_stats": 1,
        }
        self.wordlist_params = {
            "corpname": corpname,
            "wlattr": None,
            "wlmaxitems": 500,
            "wlsort": "frq",
            "wlpat": ".*",
            "wlminfreq": 1,
            "wlicase": 1,
            "wlmaxfreq": 0,
            "wltype": "simple",
            "include_nonwords": 1,
            "random": 0,
            "relfreq": 1,
            "reldocf": 0,
            "wlpage": 1,
        }


class SimpleFreqsQuery:
    """Collects data for a freqs query using simple query syntax.

    Args:
        corpname: Corpus.
        server: Server.
        config: Configuration dict.
        fcrit: Attributes to query.
        fcrit_limit: Limit attributes to those with fewer than N values.

    Methods:
        get_corp_info: Makes a preliminary corp_info call.
        set_fcrit: Determines which attributes to include in ``fcrit``.
        get_freqs: Runs the freqs API call.
        run: Executes the job and makes a DataFrame ``df`` attribute.

    Notes:
        Default gets up to 500 values per attribute: ``"wlmaxitems": 500``

    Example:
        This example gets frequency data for any word starting with "sun".

        >>> j = job.SimpleFreqsQuery("sun*", "susanne", "noske", default)
        >>> j.run()
        >>> j.df.iloc[0]
        frq           64
        rel    148.11175
        reltt      640.0
        ...
    """

    def get_corp_info(self):
        """Makes a corp_info call to retrieve corpus structures as part of a job."""
        self.corpinfo_call = CorpInfo(self.corp_info_params)
        self.corpinfo_package = Package(self.corpinfo_call, self.server, self.config)
        self.corpinfo_package.send_requests()
        self.structures_df = corp_info.structures_json(
            self.corpinfo_package.responses[0]
        )
        self.attributes = (
            self.structures_df["structure"] + "." + self.structures_df["attribute"]
        )

    def set_fcrit(self):
        """Sets fcrit to include any attributes with n =< fcrit_limit values."""
        self.get_corp_info()
        if self.fcrit_limit:
            df = self.structures_df.query("size <= @self.fcrit_limit")
            self.attributes = df["structure"] + "." + df["attribute"]
        self.freqs_params["fcrit"] = [f"{attr} 0" for attr in self.attributes]

    def get_freqs(self):
        """Makes a freqs call."""
        self.package = Package(self.call, self.server, self.config)
        self.package.send_requests()

    def run(self):
        """Executes the job."""
        if not self.freqs_params.get("fcrit"):
            self.set_fcrit()
        self.get_freqs()
        self.df = freqs.freqs_json(self.package.responses[0])

    def __init__(
        self,
        query: str,
        corpname: str,
        server: str,
        config: dict = default,
        fcrit=None,
        fcrit_limit: int = 0,
    ):
        self.query = query
        self.corpname = corpname
        self.server = server
        self.config = config
        self.fcrit_limit = fcrit_limit
        self.corp_info_params = {
            "corpname": corpname,
            "struct_attr_stats": 1,
        }
        q = simple_query(query)
        self.freqs_params = {
            "q": q,
            "corpname": corpname,
            "fcrit": fcrit,
            "freq_sort": "freq",
            "fmaxitems": 500,
            "fpage": 1,
            "group": 0,
            "showpoc": 1,
            "showreltt": 1,
            "showrel": 1,
        }
        self.call = Freqs(self.freqs_params)
