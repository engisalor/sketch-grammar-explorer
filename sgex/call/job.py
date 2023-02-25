"""Classes to execute specific API jobs."""
import pandas as pd

from sgex.call.package import Package
from sgex.call.type import CorpInfo, Freqs, Wordlist
from sgex.parse import corp_info, freqs, wordlist


class TTypeAnalysis:
    """Collects frequency data about a corpus's text types (attributes)."""

    def get_corp_info(self):
        """Makes an initial corp_info call to retrieve corpus structures."""
        self.corpinfo_call = CorpInfo(self.corp_info_params)
        self.corpinfo_package = Package(self.corpinfo_call, self.server)
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
        self.ttype_package = Package(self.ttype_calls, "noske")
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

    def __init__(self, corpname: str, server: str) -> None:
        self.corpname = corpname
        self.server = server
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
    """Collects data for a freqs query using simple query syntax."""

    def get_corp_info(self):
        """Makes an initial corp_info call to retrieve corpus structures."""
        self.corpinfo_call = CorpInfo(self.corp_info_params)
        self.corpinfo_package = Package(self.corpinfo_call, self.server)
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
        self.package = Package(self.call, self.server)
        self.package.send_requests()

    def run(self):
        """Executes the job."""
        if not self.freqs_params.get("fcrit"):
            self.set_fcrit()
        self.get_freqs()
        self.df = freqs.freqs_json(self.package.responses[0])

    def __init__(
        self, query: str, corpname: str, server: str, fcrit=None, fcrit_limit: int = 0
    ):
        self.server = server
        self.fcrit_limit = fcrit_limit
        self.corp_info_params = {"corpname": corpname}
        self.corp_info_params = {
            "corpname": corpname,
            "struct_attr_stats": 1,
        }
        self.freqs_params = {
            "q": query.simple_query(query),
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
