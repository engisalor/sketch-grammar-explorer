# Sketch Grammar Explorer

[![PyPI Latest Release](https://img.shields.io/pypi/v/sgex.svg)](https://pypi.org/project/sgex/)
[![PyPI - Python Versions](https://img.shields.io/pypi/pyversions/sgex)](https://pypi.org/project/sgex)
[![Package Status](https://img.shields.io/pypi/status/sgex.svg)](https://pypi.org/project/sgex/)
[![License](https://img.shields.io/pypi/l/sgex.svg)](https://github.com/pandas-dev/sgex/blob/main/LICENSE)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.6812334.svg)](https://doi.org/10.5281/zenodo.6812334)

## Introduction

Sketch Grammar Explorer is an API wrapper for [Sketch Engine](https://www.sketchengine.eu/), a language corpus management software useful for many types of linguistic research. The goal is to build a flexible scaffold for any kind of programmatic work with Sketch Engine and [NoSketch Engine](https://nlp.fi.muni.cz/trac/noske).

**UPDATE**

SGEX `0.7.0+` is another redesign of the package meant to facilitate enhancements. The workflow is improved and it's streamlined for adapting to SkE's updated API schema. Old methods are deprecated and unavailable in new releases.

## Installation

Clone SGEX or install it with `pip install sgex` (main dependencies are `pandas pyyaml aiohttp aiofiles`).

Get a [Sketch Engine API key](https://www.sketchengine.eu/documentation/api-documentation/#toggle-id-1). Be sure to reference SkE's documentation and schema:

`wget https://www.sketchengine.eu/apidoc/openapi.yaml -O .openapi.yaml`

## Getting started

How to use the API with a local NoSketch Engine server.

>Note: most things are identical for SkE's main server, apart from using credentials and more call types being available.
>
>SGEX currently uses the underlying Bonito API, with URLs ending in `/bonito/run.cgi`.

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
	# to define API calls
	infile: str | list | None = None,
	params: str | list | None = None,
	# to set server info
	server: str = "local",
	default_servers: dict = default_servers,
	# to supply credentials
	api_key: str | None = None,
	username: str | None = None,
	# to manage caching
	cache_dir: str = "data",
	clear_cache: bool = False,
	# to run asynchronous requests
	thread: bool = False,
	# to control request throttling
	wait_dict: dict = wait_dict,
	# to make a dry run
	dry_run: bool = False)

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

# this example uses a local server
>>> j = Job(
...	params={"call_type": "View", "corpname": "susanne", "q": 'alemma,"bird"'})
...

# run the job
>>> j.run()

# results are stored in Job.data by call type
>>> j.data.view
[View 8cdfca2 {asyn: '0', corpname: susanne, format: json, q: 'alemma,"bird"'}]

# the response gets cached in `data/<CALL_HASH>.json`: repeating the same request pulls from the cache

# the response object has a few attributes but is simplified for caching
>>> j.data.view[0].response.status
200

# data is accessible via `.text` or `.json()` (if using JSON)
>>> j.data.view[0].response.text[:50]
'{\n  "Lines": [\n    {\n      "toknum": 23026,\n      '

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

### The `Data` and `Call` classes

`Data` is a dataclass used in `Job` to store API data and make associated methods easily available. Whenever requests are made from a list of dictionary parameters, the responses are automatically sorted by `call_type`. Each call type has a list, which gets appended each time a request is made. These lists of responses can be processed using methods shared by a given call type.

Every call type is a subclass of the `call.Call` base class. All calls share some universal methods, including simple parameter verification to reduce API errors. Every subclass (`Freqs`, `View`, `CorpInfo`, etc.) can also have its own methods for data processing tasks. These methods tend to focus on manipulating JSON data; manipulating other response formats like CSV is also possible.

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

There are a couple conventions to follow to keep methods organized:

- a method should be designed for one call type
- use `self.check_format("json")` to ensure this is enforced
- its name should end in the required data format (`_from_json`)
- the docstring should specify required parameters (e.g., `"Requires a corp_info call with these parameters: {"x": "y"}`)

Feel free to suggest more methods for call types if you think they're broadly useful.

### Request throttling

Wait periods are added between calls with a `wait_dict` that defines the required increments for a number of calls. This is the standard dictionary, following SkE's [fair use policy](https://www.sketchengine.eu/fair-use-policy/):

```py
wait_dict = {"0": 9, "0.5": 99, "4": 899, "45": None}
```

In other words:

- no wait applied for 9 calls or fewer
- half a second added for up to 99 calls
- 4 seconds added for up to 899 calls
- 45 seconds added for any number above that

### Asynchronous calling

The `aiohttp` package is used to implement async requests.
This is activated with `Job(thread=True)`; it's usable with local servers only.

### Getting different data formats

Data can be retrieved in JSON, XML, CSV or TXT formats with `Job(params={"format": "csv"})` etc. Only JSON is universal: most API call types can only return some of these formats.

### How caching works

A simple filesystem cache is used to store response data. These are named with a hashing function and are accompanied with response metadata. Once a call is cached, identical requests are loaded from the cache.

>Note: response data can include credentials in several locations. SGEX strips credentials before caching URLs and JSON data.

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

>Note: numbers, URLs and other challenging tokens are parsed to some extent, but these can prevent `fuzzy_query` from finding concordances.

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

No timeouts are enforced by default, which lets expensive queries run as needed. A timeout can be enforced by adding it to `Job` kwargs. (Use this technique to pass other args to the `aiohttp` session as well.)

```py
>>> from sgex.job import Job
>>> import aiohttp

# add a very short timeout for testing
>>> timeout = aiohttp.ClientTimeout(total=0.01)

# make a call with a demanding CQL query
>>> j = Job(
...	params={
...	"call_type": "Collx",
...	"corpname": "susanne",
...	"q": "alemma,[]{,10}"})
...

# add args for session
>>> j.run(timeout=timeout)

# check for timeout exceptions
>>> j.exceptions
[(TimeoutError(), Collx 3d918a5 {corpname: susanne, format: json, q: 'alemma,[]{,10}'})]

```

>Note: even if a request is timed-out by the client, a server may still try to compute results (which can continue taking up resources on a local machine).

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

See the [Zenodo DOI](https://zenodo.org/record/6812334) for citing the software itself.
