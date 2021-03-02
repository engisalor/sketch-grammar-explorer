import requests
import time
import json
import pandas as pd
from datetime import datetime
import re
from pathlib import Path

### 
# template for freqs calls 
###

def freqs(query, fcrit, corpus = "preloaded/ecolexicon_en"):
    query_type = "freqs?"
    # set parameters
    settings = {
        "q": "q" + query,
        "fcrit": fcrit,
        "corpname": corpus
        }
    return settings, query_type