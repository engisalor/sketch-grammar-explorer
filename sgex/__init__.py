"""An API wrapper for the Sketch Engine language corpus software."""
from sgex._version import __version__
from sgex.call.package import Package
from sgex.call.query import simple_query
from sgex.call.type import (
    AttrVals,
    Call,
    Collx,
    CorpInfo,
    ExtractKeywords,
    Freqml,
    Freqs,
    Freqtt,
    Subcorp,
    Thes,
    View,
    Wordlist,
    Wsdiff,
    Wsketch,
)
