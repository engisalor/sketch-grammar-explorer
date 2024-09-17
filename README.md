# Sketch Grammar Explorer

[![PyPI Latest Release](https://img.shields.io/pypi/v/sgex.svg)](https://pypi.org/project/sgex/)
[![PyPI - Python Versions](https://img.shields.io/pypi/pyversions/sgex)](https://pypi.org/project/sgex)
[![Package Status](https://img.shields.io/pypi/status/sgex.svg)](https://pypi.org/project/sgex/)
[![License](https://img.shields.io/pypi/l/sgex.svg)](https://github.com/pandas-dev/sgex/blob/main/LICENSE)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.6812334.svg)](https://doi.org/10.5281/zenodo.6812334)

## Introduction

Sketch Grammar Explorer is an API wrapper for [Sketch Engine](https://www.sketchengine.eu/), a corpus management software useful for linguistic research. The goal is to build a flexible scaffold for any kind of programmatic work with Sketch Engine and [NoSketch Engine](https://nlp.fi.muni.cz/trac/noske).

## Installation

Clone SGEX or install it with `pip install sgex` (main dependencies are `pandas pyyaml aiohttp aiofiles`).

Get a [Sketch Engine API key](https://www.sketchengine.eu/documentation/api-documentation/#toggle-id-1). Be sure to reference SkE's documentation and schema:

`wget https://www.sketchengine.eu/apidoc/openapi.yaml -O .openapi.yaml`

## Getting started

A quick intro on the API (examples use a local NoSketch Engine server).

>Most things are identical for SkE's main server, apart from using credentials and more call types being available. SGEX currently uses the Bonito API, with URLs ending in `/bonito/run.cgi`, not newer paths like `/search/corp_info`.

### Package modules

- `job`: the primary module - makes requests and manipulates data
- `call`: classes and methods for API call types
- `query`: functions to generate/manipulate CQL queries
- `util`: utility functions

### The Job class

Calls are made with the `job` module, which can also be run as a script. The `Job` class has a few options:

```py
from sgex.job import Job

j = Job(
	# define API calls
	infile: str | list | None = None,
	params: str | dict | list | None = None,
	# set server info
	server: str = "local",
	default_servers: dict = default_servers,
	# supply credentials
	api_key: str | None = None,
	username: str | None = None,
	# manage caching
	cache_dir: str = "data",
	clear_cache: bool = False,
	# run asynchronous requests
	thread: bool = False,
	# control request throttling
	wait_dict: dict = wait_dict,
	# make a dry run
	dry_run: bool = False,
	# change verbosity
	verbose: bool = False,
	)

j.run()
```

### Making a call and accessing the response

Here's how to make a request:

```py
>>> from sgex.job import Job

# instantiate the job with options
>>> j = Job(
...	params={"call_type": "View", "corpname": "preloaded/susanne", "q": 'alemma,"bird"'},
... api_key="",		# add key
... username="",	# add name
... server="ske") 	# use SkE main server
...

# this example uses a local server (the default)
>>> j = Job(
...	params={"call_type": "View", "corpname": "susanne", "q": 'alemma,"bird"'})
...

# run the job
>>> j.run()

# get a summary
>>> dt = j.summary()
>>> for k,v in dt.items():
... 	print(k, ("<float>" if k == "seconds" else v))
...
seconds <float>
calls 1
errors Counter()

# results are stored in Job.data.<call_type_lowercase>
>>> j.data.view
[View 8cdfca2 {asyn: '0', corpname: susanne, format: json, q: 'alemma,"bird"'}]

# the response gets cached in `data/<hash>.json`: repeating the same request pulls from the cache

# data is accessible via `.text` or `.json()`
>>> j.data.view[0].response.json()["concsize"]  # the number of concordances for "bird"
12

```

### Making multiple calls

Just provide a list of call parameters (list of dict) to make more than one call.

```py
# supplying a list of calls
>>> from sgex.job import Job
>>> j = Job(
...	params=[
...	{"call_type": "CorpInfo", "corpname": "susanne"},
... {"call_type": "View", "corpname": "susanne", "q": 'alemma,"bird"'},
... {"call_type": "Collx", "corpname": "susanne", "q": 'alemma,"bird"'}])
...
>>> j.run()
>>> j.data
<class 'sgex.call.Data'>
collx (1)    [Collx 26d29b1 {corpname: susanne, format: json, q: 'alemma,"bird"'}]
corpinfo (1)    [Corp_info 9c08055 {corpname: susanne, format: json}]
view (1)    [View 8cdfca2 {asyn: '0', corpname: susanne, format: json, q: 'alemma,"bird"'}]

```

Or supply a JSON, JSONL or YAML file with calls:

```json
// test/example.jsonl
{"call_type": "Collx", "corpname": "susanne", "q": "alemma,\"apple\""}
{"call_type": "Collx", "corpname": "susanne", "q": "alemma,\"carrot\""}
{"call_type": "Collx", "corpname": "susanne", "q": "alemma,\"lettuce\""}
```

```py
# supplying a file of calls
>>> from sgex.job import Job
>>> j = Job(infile="test/example.jsonl")
>>> j.run()
>>> j.data
<class 'sgex.call.Data'>
collx (3)    [Collx bc5d89b {corpname: susanne, format: json, q: 'alemma,"apple"'}, Collx 19495d0 {corpname: susanne, format: json, q: 'alemma,"carrot"'}, Collx 7edee07 {corpname: susanne, format: json, q: 'alemma,"lettuce"'}]

```

### Making multiple calls for concordances

The `View` call retrieves concordances by page, defaulting to page 1. Its `fromp` and `pagesize` parameters adjust the current page and max number of concordances per page. Using a large `pagesize` is often fine to get data in one request, but it may be better to use several. For this, try `Job.run_repeat()`, which gets the first page, calculates how many pages remain, and then gets remaining pages (or up to `max_pages`, if defined).

This example gets all the hits for `work` in the Susanne corpus in sets of 10 concordances per page. There are 93 in total, meaning that 10 requests are made (`fromp=1` through `fromp=10`).

```py
>>> from sgex.job import Job

# run job
>>> j = Job(params={"call_type": "View", "corpname": "susanne", "q": 'aword,"work"', "fromp": 1, "pagesize": 10})
>>> j.run_repeat(max_pages=0) # optionally set max_pages to stop after n pages

# the 93 concordances were retrieved in 10 calls
>>> j.data.view[0].response.json()["concsize"] == 93
True
>>> len(j.data.view) == 10
True

```

### Manipulating data

Response data can be manipulated by accessing the lists of calls stored in `Job.data`. A few methods are included so far, such as `Freqs.df_from_json()`, which transforms a JSON frequency query to a DataFrame.

```py
# convert frequency JSON to a Pandas DataFrame
>>> from sgex.job import Job
>>> j = Job(
... params={
... "call_type": "Freqs",
... "corpname": "susanne",
... "fcrit": "doc.file 0",
... "q": 'alemma,"bird"'})
>>> j.run()
>>> df = j.data.freqs[0].df_from_json()
>>> df.head(3)
   frq         rel        reltt        fpm value attribute     arg nicearg corpname  total_fpm  total_frq fmaxitems
0    7  3625.97107  2892.561983  46.534509   A11  doc.file  "bird"    bird  susanne      79.77         12      None
1    2  1093.37113   872.219799  13.295574   N08  doc.file  "bird"    bird  susanne      79.77         12      None
2    1   525.59748   419.287212   6.647787   G04  doc.file  "bird"    bird  susanne      79.77         12      None

```

## Next steps

A few more considerations for doing corpus linguistics with SGEX.

### The `Data` and `Call` classes

`Data` is a dataclass used in `Job` to store API data and make associated methods easily available. Whenever requests are made from a list of dictionary parameters, the responses are automatically sorted by `call_type`. Each call type has a list, which gets appended each time a request is made. These lists of responses can be processed using methods shared by a given call type.

Every call type is a subclass of the `call.Call` base class. All calls share some universal methods, including simple parameter verification to reduce API errors. Every subclass (`Freqs`, `View`, `CorpInfo`, etc.) can also have its own methods for data processing tasks. These methods tend to focus on manipulating JSON data, which is the only complete format for the API; manipulating other response formats like CSV is also possible.

>At least while SGEX is in beta, existing methods aren't stable for production purposes: using your own custom method, like the following example, is a safer bet.

### Custom corpus data manipulation techniques

Adding custom methods to a call type is easy:

```py
>>> from sgex.job import Job
>>> from sgex.call import CorpInfo

# write a new method
>>> def new_method_from_json(self) -> str:
...     """Returns a string of corpus structures."""
...     self.check_format()
...     _json = self.response.json()
...     return " ".join([k.replace("count", "") for k in _json.get("sizes").keys()])
>>> CorpInfo.new_method_from_json = new_method_from_json

# run the job
>>> j = Job(
... clear_cache=True,
... params={"call_type": "CorpInfo", "corpname": "susanne", "struct_attr_stats": 1})
>>> j.run()

# use the method
>>> j.data.corpinfo[0].new_method_from_json()
'token word doc par sent'

```

Feel free to suggest more methods for call types if you think they're useful. Be sure to explain the purpose and required parameters in the docstring (e.g., `"Requires a corp_info call with these parameters: {"x": "y"}`).

### Request throttling

Wait periods are added between calls with a `wait_dict` that defines the required increments for a number of calls. This is the standard dictionary, following SkE's [fair use policy](https://www.sketchengine.eu/fair-use-policy/):

```py
wait_dict = {"0": 9, "0.5": 99, "4": 899, "45": None}
```

In other words:

- no wait applied for 9 calls or fewer
- 0.5 seconds added for up to 99 calls
- 4 seconds added for up to 899 calls
- 45 seconds added for any number above that

### Asynchronous calling

The `aiohttp` package is used to implement async requests.
This is activated with `Job(thread=True)`; it's usable with local servers only.

The number of connections for async calling is adjustable by adding a kwarg when running a job. The default of 20 should increase rates while reducing errors, although this depends on how many calls are made, their complexity, and the hardware.

```py
Job.run(connector=aiohttp.TCPConnector(limit_per_host=int))
```

>If a large asynchronous job raises a few exceptions caused by the server struggling to handle requests, it's often simpler to just run the job again. This retries failed calls and loads successful ones from the cache. Trying to adjust the `connector` to eliminate one or two exceptions out of 1,000 calls isn't necessary.
>
>If calls are complex and the corpus is large, using sequential calling might be the best option.

### Getting different data formats

Data can be retrieved in JSON, XML, CSV or TXT formats with `Job(params={"format": "csv"})` etc. Only JSON is universal: most API call types can only return some of these formats.

### How caching works

A simple filesystem cache is used to store response data. These are named with a hashing function and are accompanied with response metadata. Once a call is cached, identical requests are loaded from the cache. Calls with `format="json"` and no exceptions or SkE errors get cached. Data in other formats (CSV, XML) are always cached since error handling isn't implemented.

>Response data can include credentials in several locations. SGEX strips credentials before caching URLs and JSON data, although inspecting data before sharing it is still prudent.

### Simple queries

`simple_query` approximates this query type in SkE: enter a phrase and a CQL rule is returned. The search below uses double hyphens to include tokens w/ or w/o hyphens or spaces; wildcard tokens are also possible.

```py
>>> from sgex.query import simple_query
>>> simple_query("home--made * recipe")
'( [lc="homemade" | lemma_lc="homemade"] | [lc="home" | lemma_lc="home"] [lc="made" | lemma_lc="made"] | [lc="home-made" | lemma_lc="home-made"] | [lc="home" | lemma_lc="home"] [lc="-" | lemma_lc="-"] [lc="made" | lemma_lc="made"] ) [lc=".*" | lemma_lc=".*"][lc="recipe" | lemma_lc="recipe"]'

```

### Fuzzy queries

`fuzzy_query` takes a sentence or longer phrase and converts it into a more forgiving CQL rule. This can be helpful to relocate an extracted concordance or find similar results elsewhere. The returned string is formatted to work with `word` or `word_lowercase` as a default attribute.

```py
>>> from sgex.query import fuzzy_query
>>> fuzzy_query("Before yesterday, it was fine, don't you think?")
'"Before" "yesterday" []{,1} "it" "was" "fine" []{,3} "you" "think"'
>>> fuzzy_query("We saw 1,000.99% more visitors at www.example.com yesterday")
'"We" "saw" []{,6} "more" "visitors" "at" []{,2} "yesterday"'

```

>Numbers, URLs and other challenging tokens are parsed to some extent, but these can prevent `fuzzy_query` from finding concordances.

### Checking hashes

To cache data, each unique call is identified by hashing an ordered JSON representation of its parameters. Hashes can be derived from input data (the parameters you write) and response data (the parameters as stored in a JSON API response). Accessing hashes can be done as such:

```py
>>> from sgex.job import Job
>>> from sgex.call import CorpInfo

# get shortened hash from input parameters
>>> c = CorpInfo({"corpname": "susanne", "struct_attr_stats": 1})
>>> c.hash()[:7]
'9c28c7a'

# send request
>>> j = Job(
...	params={"call_type": "CorpInfo", "corpname": "susanne", "struct_attr_stats": 1})
...
>>> j.run()

# get shortened hash from response
>>> j.data.corpinfo[0].hash()[:7]
'9c28c7a'

```

### Adding a timeout / changing `aiohttp` behavior

Timeouts are disabled for the `local` server, which lets expensive queries run as needed. Other servers use the `aiohttp` default of 5 minutes. Enforce a custom timeout by adding it to `Job` kwargs. (Use this technique to pass other args to the `aiohttp` session as well.)

```py
>>> from sgex.job import Job
>>> import aiohttp

# add a very short timeout for testing
>>> timeout = aiohttp.ClientTimeout(sock_read=0.01)

# design a call with a demanding CQL query
>>> j = Job(
...	params={
...	"call_type": "Collx",
...	"corpname": "susanne",
...	"q": "alemma,[]{,10}"})
...

# run with additional session args
>>> j.run(timeout=timeout)


# check for timeout exception [(error, call, index), ...]
>>> isinstance(j.errors[0][0], aiohttp.client_exceptions.ServerTimeoutError)
True

```

>Even if a request is timed-out by the client, a server may still try to compute results (and continue taking up resources on a local machine, causing unexpected exceptions).

### Example: make a stratified random sample with a series of API calls

Data from different call types can be utilized together to construct more complex queries and custom operations. For example, the `random sample` feature in Sketch Engine's interface uses simple randomization, yet some analyses might require a stratified sampling technique (taking a separate random sample for each category in a text type). This can be done with the code below.

This includes three API call types:

1. a `CorpInfo` call
2. a `AttrVals` call
3. a series of `View` calls (64, requested concurrently)

It retrieves 5 random concordances for each `doc.file` text type in the `susanne` corpus for cases of "the" and a following token.

```py
>>> from sgex.job import Job

# 1. check the corpus's attributes
>>> j = Job(params={"call_type": "CorpInfo", "corpname": "susanne", "struct_attr_stats": 1})
>>> j.run()
>>> j.data.corpinfo[0].structures_from_json()
  structure  attribute  size
0      font       type     2
0      head       type     2
0       doc       file    64
1       doc          n    12
2       doc  wordcount     1

# 2. get values for one text type
# (make sure avmaxitems is >= the size of the text type)
>>> j0 = Job(params={"call_type": "AttrVals", "corpname": "susanne", "avattr": "doc.file", "avmaxitems": 1000000})
>>> j0.run()
>>> values = j0.data.attrvals[0].response.json()["suggestions"]

# the query ['a<default_attribute>,"<cql_rule>"', "r<sample_size>"]
>>> q = [f'alemma,"the" []', "r5"]
>>> call_template = {
...    "call_type": "View",
...    "corpname": "susanne",
...    "viewmode": "sen",
...    "pagesize": 1000, # make greater than "r<int>"" to get everything in one request
...    "attrs": "word,tag,lemma",
...    "attr_allpos": "all"}

# generate list of calls
>>> calls = []
>>> for value in values:
...    within = f' within <doc file="{value}" />'
...    calls.append(call_template | {"q": [q[0] + within, q[1]]})

# 3. execute job
>>> j1 = Job(params=calls, thread=True)
>>> j1.run()

# process data as needed
# (print the query for the first sample)
>>> print(j1.data.view[0].response.json()["request"]["q"])
['alemma,"the" [] within <doc file="A01" />', 'r5']

# (print the KWICs for the first sample)
>>> for x in range(5):
...    kwic = j1.data.view[0].response.json()["Lines"][x]["Kwic"]
...    tokens = []
...    for dt in kwic:
...        if dt["class"] != "attr":
...            tokens.append(dt["str"].strip())
...    print(" ".join(tokens))
the jury
the Fulton
the state
the recommendations
the jury

```

## Running as a script

If the repo is cloned and is the current working directory, SGEX can be run as a script as such:

```sh
# gets collocation data from the Susanne corpus for the lemma "bird"
python sgex/job.py -p '{"call_type": "Collx", "corpname": "susanne","q": "alemma,\"bird\""}'
```

Basic commands are available to run as a script for downloading data. Example: one could read a list of API calls from a file (`-i "<myfile.json>"`) and send requests to the SkE server (`-s "ske"`). More complex tasks still require importing modules in Python.

Run SGEX with `--help` for up-to-date options.

```sh
python sgex/job.py --help

usage: SGEX [-h] [-k API_KEY] [--cache-dir CACHE_DIR] [--clear-cache] [--data DATA] [--default-servers DEFAULT_SERVERS] [--dry-run] [-i [INFILE ...]] [-p [PARAMS ...]] [-s SERVER] [-x] [-u USERNAME] [-w WAIT_DICT]
```

|arg|example|description|
|---|---|---|
| -k --api-key | `"1234"` | API key, if required by server |
| --cache-dir | `"data"` (default) | cache directory location |
| --clear-cache | (disabled by default) | clear the cache directory (ignored if `--dry-run`) |
| --data | (reserved) | placeholder for API call data |
| --default-servers | `'{"server_name": "URL"}'` | settings for default servers |
| --dry-run | (disabled by default) | print job settings |
| -i --infile |	`"api_calls.json"` | file(s) to read calls from |
| -p --params | `'{"call_type": "Collx", "corpname": "susanne","q": "alemma,\"bird\""}'`	| JSON/YAML string(s) with a dict of params |
| -s --server | `"local"` (default) | `local`, `ske` or a URL to another server |
| -x, --thread | (disabled by default) | run asynchronously, if allowed by server |
| -u --username | `"J. Doe"` | API username, if required by server |
| -v --verbose | (disabled by default) | print details while running |
| -w --wait-dict | `'{"0": 10, "1": null}'` (wait zero seconds for =<10 calls and 1 second for 10<) | wait period between calls |

## Environment variables

Environment variables can be set by exporting them or using an `.env` file. When used as env variables, argument names are just converted to uppercase and given a prefix.

### Example file

```bash
# .env
SGEX_API_KEY="<KEY>"
SGEX_CACHE_DIR="<PATH>"
SGEX_CLEAR_CACHE=False
SGEX_DRY_RUN=True
SGEX_INFILE="<FILE>"
SGEX_SERVER="ske"
SGEX_USERNAME="<USER>"
```

### Example usage

```bash
# export variables in .env
set -a && source .env && set +a

# run SGEX
python sgex/job.py # add args here

# unset variables
unset ${!SGEX_*}
```

## About

SGEX has been developed to meet research needs at the University of Granada Translation and Interpreting Department. See the [LexiCon research group](http://lexicon.ugr.es/) for related projects.

The name refers to sketch grammars, which are series of generalized corpus queries in Sketch Engine (see their [bibliography](https://www.sketchengine.eu/bibliography-of-sketch-engine/)).

Questions, suggestions and support are welcome.

## Citation

If you use SGEX, please cite it. This paper introduces the package in the context of doing collocation analysis:

```bibtex
@inproceedings{isaacsAggregatingVisualizingCollocation2023,
	address = {Lisbon, Portugal},
	title = {Aggregating and {Visualizing} {Collocation} {Data} for {Humanitarian} {Concepts}},
	url = {https://ceur-ws.org/Vol-3427/short11.pdf},
	booktitle = {Proceedings of the 2nd {International} {Conference} on {Multilingual} {Digital} {Terminology} {Today} ({MDTT} 2023)},
	publisher = {CEUR-WS},
	author = {Isaacs, Loryn and León-Araúz, Pilar},
	editor = {Di Nunzio, Giorgio Maria and Costa, Rute and Vezzani, Federica},
	year = {2023},
}
```

See [Zenodo](https://zenodo.org/record/6812334) for citing specific versions of the software.
