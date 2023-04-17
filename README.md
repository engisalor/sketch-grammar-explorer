# Sketch Grammar Explorer

[![PyPI Latest Release](https://img.shields.io/pypi/v/sgex.svg)](https://pypi.org/project/sgex/)
[![PyPI - Python Versions](https://img.shields.io/pypi/pyversions/sgex)](https://pypi.org/project/sgex)
[![Package Status](https://img.shields.io/pypi/status/sgex.svg)](https://pypi.org/project/sgex/)
[![License](https://img.shields.io/pypi/l/sgex.svg)](https://github.com/pandas-dev/sgex/blob/main/LICENSE)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.6812334.svg)](https://doi.org/10.5281/zenodo.6812334)

- [Sketch Grammar Explorer](#sketch-grammar-explorer)
  - [Introduction](#introduction)
  - [Setup](#setup)
  - [TL;DR](#tldr)
  - [Quickstart](#quickstart)
    - [1. Setting a configuration dictionary](#1-setting-a-configuration-dictionary)
    - [2. Making a `corp_info` API call](#2-making-a-corp_info-api-call)
    - [3. Parsing results to a DataFrame](#3-parsing-results-to-a-dataframe)
  - [Package structure](#package-structure)
    - [Configuration: `sgex.config`](#configuration-sgexconfig)
    - [Exporting content: `sgex.io`](#exporting-content-sgexio)
    - [Creating call objects: `sgex.<CallType>`](#creating-call-objects-sgexcalltype)
    - [Assembling CQL rules: `sgex.simple_query`](#assembling-cql-rules-sgexsimple_query)
    - [Managing calls: `sgex.call`](#managing-calls-sgexcall)
    - [Packaging and sending calls: `sgex.Package`](#packaging-and-sending-calls-sgexpackage)
    - [Workflow examples](#workflow-examples)
      - [Running complex tasks: `sgex.call.job`](#running-complex-tasks-sgexcalljob)
      - [Parsing data: `sgex.parse`](#parsing-data-sgexparse)
  - [API usage notes](#api-usage-notes)
  - [Security](#security)
    - [API credentials](#api-credentials)
    - [Data storage](#data-storage)
  - [About](#about)
  - [Citation](#citation)

## Introduction

Sketch Grammar Explorer (SGEX) is a Python package for using the [Sketch Engine](https://www.sketchengine.eu/) API. Sketch Engine is a language corpus management software useful for many types of linguistic research. The goal of SGEX is to develop a flexible scaffold for any kind of programmatic work with Sketch Engine and [NoSketch Engine](https://nlp.fi.muni.cz/trac/noske).

**NOTE**

SGEX `0.6.0+` is a complete redesign of the package and its previous functions may become deprecated. `0.5.5` is the last version before the switch. Its documentation has [moved](https://github.com/engisalor/sketch-grammar-explorer/blob/main/README_deprecated.md) and import paths have changed.

## Setup

Clone SGEX or install it with `pip install sgex`

Dependencies:
- required: `pandas pyyaml requests requests-cache`
- optional: `keyring openpyxl defusedxml`

## TL;DR

An abbreviated example of SGEX for making calls to Sketch Engine.

```python
import sgex

# add API credentials to the server configuration
sgex.config.default["ske"] |= {"username": "J. Doe", "api_key": "1234"}

# define API calls
calls = [
    # the first freqs call is complete (has all the needed parameters)
    sgex.Freqs({
        "format": "csv",
        "q": 'alemma,"eat"',
        "corpname": "preloaded/susanne",
        "fcrit": "doc.file 0",
        }),
    # successive freqs calls will reuse previous parameters
    sgex.Freqs({"q": 'alemma,"sleep"'})]

# package calls
package = sgex.Package(calls, "ske")

# send requests
package.send_requests()

# access response data
print(package.responses[0].text)
"corpus","preloaded/susanne"
"subcorpus","-"
"concordance size","8"
"query","Query:""eat"""
"File name", "Frequency", "Relative density", "Freq. per million", "Relative in text types"
"N01",3, 2245.61107, 19.94336, 1194.26752
"J17",1, 812.23542, 6.64779, 431.96544
"N08",1, 820.02835, 6.64779, 436.10990
...
```

## Quickstart

The following code shows in detail all the steps needed for a sample workflow:

1. Setting a configuration dictionary
2. Making a `corp_info` API call
3. Parsing the result into a pandas DataFrame

This requires [getting a Sketch Engine API key](https://www.sketchengine.eu/documentation/api-documentation/#toggle-id-1).

After trying out this basic example, see other sections on more advanced usage.

### 1. Setting a configuration dictionary

There are several ways to supply configuration settings to SGEX. This example modifies the default settings to show what each element means.

```python
import sgex

# print default configuration settings
print(sgex.config.default)
# this dictionary contains server information
{
  # a local NoSketch Engine server
  'noske': {
    # URL
    'host': 'http://localhost:10070/bonito/run.cgi',
    # enable asynchronous calling
    'asynchronous': True},
  # Sketch Engine's server
  'ske': {
    # credentials
    'username': '<user>',
    'api_key': '<key>',
    # URL
    'host': 'https://api.sketchengine.eu/bonito/run.cgi',
    # settings for throttling requests
    'wait': {
      '0': 1, # wait 0 seconds for 1 call
      '2': 99, # wait 2 seconds for 2-99 calls
      '5': 899, # wait 5 seconds for 100-899 calls
      '45': None}}} # wait 45 seconds for 900+ calls

# add your API credentials for making calls to the "ske" server
sgex.config.default["ske"] |= {"username": "J. Doe", "api_key": "1234"}
```

### 2. Making a `corp_info` API call

Each type of API call has its own Python class (e.g., `CorpInfo`), which is a child of the generic `Call` class. To make API calls, start by creating `Call` objects.

Calls are added to a `Package` class, which prepares requests and manages their execution. A `Package` can be inspected to make sure everything looks good before sending calls. Packages also expose other settings for more advanced usage.

API data gets cached locally after successful requests. Running the same request again retrieves data from the cache instead of making an API call. Cache `session` settings are customizable: see the [requests-cache](https://requests-cache.readthedocs.io/) package for details.

```python
import sgex

# indicate which server to use
server = "ske"

# define a call
call = sgex.CorpInfo({"corpname": "preloaded/susanne"})

# package the call
package = sgex.Package(call, server)

# config dicts can also be passed explicitly
# package = sgex.Package(call, server, config_dict)

# inspect the package details
print(package.calls)
[CORP_INFO(2a8c0b24) {'api_key': '1234', 'username': 'J. Doe', 'corpname': 'preloaded/susanne'}]

print(package.calls[0].request)
<Request [GET]>

# send the request
package.send_requests()
```

### 3. Parsing results to a DataFrame

The `sgex.parse` subpackage has modules for processing results based on call type and format. As Sketch Engine has many purposes, `parse` is only meant to offer examples of how to manipulate its data.

The example below takes `corp_info` JSON content and converts it into a DataFrame.

```python
import sgex

# get the call response
response = package.responses[0]

# inspect the response
print(response.url)
'https://api.sketchengine.eu/bonito/run.cgi/corp_info?corpname=preloaded/susanne'

print(response.json())
{'wposlist': [['adjective', 'JJ.*'], ['adverb', 'RR.*'], ['conjuction', 'CC.*'], ['determiner', 'AT.*'], ... }

# parse the response
sgex.parse.corp_info.sizes_json(response)
  structure    size
0     token  150426
1      word  128998
2       doc     149
...
```

## Package structure

### Configuration: `sgex.config`

Configuration dictionaries can be passed to SGEX in several formats with the `config.load` convenience function. It can parse these sources:

- a JSON/YAML file (``config.yml``)
- a JSON-formatted environment variable string (``SGEX_CONFIG_JSON``)
- a JSON-formatted string (``"{<JSON content>}"``)

```python
# example use of environment variables to load configuration
import json
import os
from sgex.config import load, default

# make a config dict with credentials
config = {"ske": {**default["ske"], **{"username": "J. Doe", "api_key": "1234"}}}

# add the environment variable (for testing purposes)
os.environ["SGEX_CONFIG_JSON"] = json.dumps(config)

# load config from the environment
print(load("SGEX_CONFIG_JSON"))
{'ske': {'api_key': '1234', 'host': 'https://api.sketchengine.eu/bonito/run.cgi', 'username': 'J. Doe', 'wait': {'0': 1, '2': 99, '5': 899, '45': None}}}
```

### Exporting content: `sgex.io`

These are functions to load and save data. The easiest way to export data from `Response` objects is to use the `sgex.io.export_content` function. If an error is raised when trying to export data, check ``response.content`` for any internal SkE errors and try making the same API call with ``"format": "json"``.

```python
from sgex.io import export_content

# get response from package
response = package.responses[0]

# export it
export_content(response, "my-filename")
```

### Creating call objects: `sgex.<CallType>`

Each API call type has its own class, which is a child of the `Call` base class. `Call` contains a basic validation function to make sure improperly created calls are identified before requests get sent.

Each call type consists of `type`, `parameters`, and `required parameters`. The example below shows the required parameters for several call types.

```python
import sgex

print(sgex.Freqs({}).required)
{'fcrit', 'q', 'corpname'}

print(sgex.Wordlist({}).required)
{'wltype', 'wlattr', 'corpname'}

print(sgex.View({}).required)
{'q', 'corpname'}
```

**Generating large call lists**

Call classes can be used to generate many calls. The example below makes several `freqs` calls using list iteration. While this is convenient, to help reduce network traffic be watchful for when multiple calls could be combined.

```python
import sgex

# define queries
queries = ["apple", "banana", "peach", "strawberry", "blueberry"]

# make call list using iteration
calls = [
  sgex.Freqs({
    "q": f'alemma,"{q}"',
    "corpname": "<my corpus>",
    "fcrit": "doc.id 0",
    }) for q in queries]

# print results
print(calls)
[FREQS(*) {'q': 'alemma,"apple"', 'corpname': '<my corpus>', 'fcrit': 'doc.id 0'},
FREQS(*) {'q': 'alemma,"banana"', 'corpname': '<my corpus>', 'fcrit': 'doc.id 0'},
...

# the missing key in FREQS(<key>) isn't computed until calls get packaged
```

### Assembling CQL rules: `sgex.simple_query`

Some functions are included for simplifying the generation of [Corpus Query Language](https://www.sketchengine.eu/documentation/corpus-querying/) rules. `simple_query()` simulates the "Simple" feature in Sketch Engine: words or phrases can be supplied and their CQL representation is returned. A few wildcards also make rules more flexible, although behavior may not always match Sketch Engine's user interface.

- Question marks `?` for any single character
- Asterisks `*` for any token or string of characters
- Double hyphens `--` for flexible hyphenation (w/ hyphen, w/o hyphen, a single word)

```python
import sgex

# example with hyphen
print(sgex.simple_query("flour-based recipe"))
'q( [lc="flour-based" | lemma_lc="flour-based"] | [lc="flour" | lemma_lc="flour"] [lc="-" | lemma_lc="-"] [lc="based" | lemma_lc="based"] )[lc="recipe" | lemma_lc="recipe"]'

# example with double hyphen and asterisk token
print(sgex.simple_query("flour--based *"))
'q( [lc="flourbased" | lemma_lc="flourbased"] | [lc="flour" | lemma_lc="flour"] [lc="based" | lemma_lc="based"] | [lc="flour-based" | lemma_lc="flour-based"] | [lc="flour" | lemma_lc="flour"] [lc="-" | lemma_lc="-"] [lc="based" | lemma_lc="based"] )[lc=".*" | lemma_lc=".*"]'
```

### Managing calls: `sgex.call`

`sgex.call` has everything needed for managing calls, although accessing it isn't generally necessary, since `Package` initialization handles the below features.

**Recycling parameters**

`propagate()`, recycles parameters across calls of the same type. Call parameters are reused unless defined explicitly in subsequent calls. Only the first call (of the same type) is complete, and the proceeding calls only contain new parameters to define. Parameter recycling stops if a different call type appears; write out a complete set of parameters again if needed.

```python
calls = [
    # the first call in a list always needs to be complete
    sgex.Freqs({
        "format": "csv",
        "q": 'alemma,"rock"',
        "corpname": "preloaded/susanne",
        "fcrit": "doc.file 0",
        }),
    # the next two freqs calls will recycle previous parameters
    sgex.Freqs({"q": 'alemma,"stone"'}),
    sgex.Freqs({"q": 'alemma,"pebble"'}),
    sgex.Wordlist({"corpname": "preloaded/susanne"}),
    # this freqs call will be incomplete!
    sgex.Freqs({"q": 'alemma,"sand"'})]
```

**Normalizing Call dictionaries**

`normalize_dt` standardizes API call formatting. This helps avoid making duplicate calls when parameters are functionally equivalent. It's most apparent with parameters that take lists. These two `fcrit` values return the same results regardless of list order.

- `{"fcrit": ["doc.genre 0", "doc.editor 0", "doc.year 0"]}`
- `{"fcrit": ["doc.editor 0", "doc.year 0", "doc.genre 0"]}`

Normalization is limited, however, so it's best to follow consistent formatting when making calls. The two queries below are the same but the extra space doesn't get normalized (yet).

- `{"q": 'alemma,"stone"'}`
- `{"q": 'alemma, "stone"'}`

**Cached content key creation**

To manage caching with `requests-cache`, sorted dictionaries that include the call type and normalized call parameters get passed to a custom hashing function (`create_custom_key`). The keys assigned to calls can be accessed as shown below. Keys correspond to cache filenames, table rows, etc., depending on the backend.

```python
# show part of key for each call
print(package.calls)
[FREQS(79f8510c) {'format': 'csv', 'q': 'alemma,"rock"', 'corpname': 'preloaded/susanne', 'fcrit': 'doc.file 0'}, FREQS(011b9079) {'q': 'alemma,"stone"', 'fcrit': 'doc.file 0', 'format': 'csv', 'corpname': 'preloaded/susanne'}, ...]

# show full key for one call
print(package.calls[0].key)
'79f8510cc16b10bb'
```

### Packaging and sending calls: `sgex.Package`

`Package` is how making and executing API calls is managed.

**Methods for sending calls**

- `Package.send_requests()` executes a list of calls sequentially, following throttling instructions in `config["<server>"]["<wait>"]` if provided
- `Package.send_async_requests()` executes a list of calls asynchronously if `config["<server>"]["asynchronous"] = True`

Both methods have some error handling to prevent repeating calls if something is misconfigured, but still test large jobs beforehand to avoid issues.

**Server wait times**

Servers may require waiting between calls. SGEX manages waiting for the Sketch Engine server following their [Fair Use Policy](https://www.sketchengine.eu/fair-use-policy/) guidelines. If a custom server requires waiting, this can be enabled by adding a `wait` entry in the configuration, like below:

```yml
ske:           # server name
  wait:        # wait dictionary
  "0": 1       # 0s for 1 call
  "5": 100     # 5s for 2-99 calls
  "10": null   # 10s for 100+ calls
```

Call throttling is implemented as a `Request.response` hook, meaning that waiting is only applied for calls that haven't been cached yet.

**Asynchronous calling**

For local servers, asynchronous calling can increase performance substantially. By default, the number of threads adjusts according to the number of CPUs available (see `max_workers` for [concurrent.futures](https://docs.python.org/3/library/concurrent.futures.html#concurrent.futures.ThreadPoolExecutor)).

**Customizing Package settings**

The `requests-cache` session can be modified to use different backends (Redis, SQLite, filesystem, etc.), as well as other features. This is an example of Package attributes:

```python
Package.calls: list  # list of calls
Package.server: str  # server to call
Package.halt: bool   # whether to stop a job on error
Package.errors: set  # errors encountered
Package.loglevel: str  # logging level
Package.max_workers: int  # threads for asynchronous calls
Package.responses: list  # call responses
Package.max_responses: int  # max items to store in `Package.responses` (for large jobs)
Package.session_params: dict(  # parameters for the `requests-cache` session
    cache_name="data",
    serializer="json",
    backend="filesystem",
    ignored_parameters=credential_parameters,
    key_fn=call.create_custom_key,
)
Package.config: dict  # server configuration
Package.session: requests_cache.CachedSession  # session object
```

Settings can be changed by adding additional `kwargs` during instantiation. Print `package.__dict__` before making calls to see all options at once.

**Clearing the cache**

The `session` attribute for a `Package` can be used to perform any tasks on the cache, e.g., clearing the cache: `Package.session.cache.clear()`. This may be more convenient than importing a session independently via `requests-cache`.

### Workflow examples

The features described so far offer the building blocks for all sorts of linguistic analyses with Sketch Engine. In contrast, these examples are for reference purposes. They may inform your workflow and be useful for specific needs, but they aren't a one-size-fits-all solution. **Modules here may change without warning**.

#### Running complex tasks: `sgex.call.job`

These classes combine multiple API calls, parsing methods, etc., to execute larger jobs with a single command.

**Text type analysis**

`TTypeAnalysis` automates the steps for generating a DataFrame describing the corpus's composition.

```python
from sgex.call.job import TTypeAnalysis

# prepare the job
ttypes = TTypeAnalysis("susanne", <server>)

# run the job
ttypes.run()

# view the results
print(ttypes.df.head(3))
    str  frq  relfreq  attribute
0  ital  263  1748.37  font.type
1  bold   38   252.62  font.type
2   maj  182  1209.90  head.type
```

**Simple frequency query**

`SimpleFreqsQuery` automates making a `freqs` call with Simple Query syntax and processing JSON data into a DataFrame.

```python
from sgex.call.job import SimpleFreqsQuery

# prepare the job
query = SimpleFreqsQuery("sleep", "susanne", "noske")

# run the job
query.run()

# view the results (each row is a corpus attribute/text type)
print(query.df.head(3))
   frq         rel        reltt  ...  total_fpm total_size fmaxitems
0   24     0.00000     0.000000  ...     159.55         24       500
1   24     0.00000     0.000000  ...     159.55         24       500
2    9  2245.61107  3582.802548  ...     159.55         24       500

[3 rows x 12 columns]
```

#### Parsing data: `sgex.parse`

`parse` contains techniques for parsing each API call type. These functions generally apply to JSON responses, as this format offers the most detailed content to build data sets with. Since many types of queries are possible in Sketch Engine, `parse` just includes a few use cases.

```python
# docstring for a parsing function
def freqs_json(response: Response) -> pd.DataFrame:
    Converts a single-/multi-block freqs JSON response to a DataFrame.

    Args:
        response: Response object.

    Example:
        >>> call = Freqs({
            "corpname": "susanne",
            "q": 'alemma,"day"',
            "fcrit": "doc.file 0"
            })
        >>> p = Package(call, "noske", default)
        >>> p.send_requests()
        >>> df = freqs.freqs_json(p.responses[0])
        >>> df.iloc[0]
        frq                     8
        rel              426.2205
        reltt         3286.770748
        ...
```

## API usage notes

**Sketch Engine vs NoSketch Engine**

These versions of the software [behave differently](https://www.sketchengine.eu/nosketch-engine/), so make sure data are comparable if using both for an analysis. A convenient way to implement NoSketch Engine is with this [NoSketch Engine Docker project](https://github.com/ELTE-DH/NoSketch-Engine-Docker).

**Available formats**

API responses have JSON content by default. Other formats can be downloaded by adding `"format": "<format>"` to `Call` parameters (`["json", "xml", "xlsx", "csv", "txt"]`). Call types (`freqs`, `view`, etc.) are only compatible with certain formats, depending on the shape of the data. Only JSON is universally available.

**Too many requests**

Sketch Engine blocks API activity outside of their FUP. While learning the API, test calls selectively, slowly, and avoid repeated identical calls.

**API behavior**

To learn more about the API, it's helpful to inspect network activity while using the Sketch Engine interface. Importantly, some internal API methods exist that won't work if copy-pasted into SGEX calls.

**Double-checking accuracy**

Before relying heavily on the API, it's a good idea to practice trying the same queries both in a web browser and via API to make sure the results are identical.

## Security

Some considerations for using SGEX.

### API credentials

Response data can include credentials in several locations and should be removed before storing or sharing. SGEX mitigates the exposure of credentials in saved data by 1) instructing `requests-cache` to strip credentials from URLs and 2) executing a custom hook to redact JSON response data before it gets cached.

### Data storage

Data can be stored more securely by using a custom serializer with `requests-cache`, as in the example below, which encrypts/decrypts data. When storing unencrypted `pickle` data, they recommend using the [safe_pickle_serializer](https://requests-cache.readthedocs.io/en/stable/user_guide/security.html).

```python
from requests_cache import SerializerPipeline, Stage, pickle_serializer
from cryptography.fernet import Fernet

# make a key (store this safely once generated)
key = Fernet.generate_key()
f = Fernet(key)

# define the serializer
encrypt_pickle_serializer = SerializerPipeline(
    [pickle_serializer, Stage(dumps=f.encrypt, loads=f.decrypt)], is_binary=True)

# add the serializer to the session
session_params = dict(
    serializer=encrypt_pickle_serializer,
    <other session parameters>)

# make calls and test the encryption of cache data
p = Package(<calls>, <server>, session_params=session_params)
p.send_requests()
```

## About

SGEX has been developed to meet research needs at the University of Granada (Spain) Translation and Interpreting Department. See the [LexiCon research group](http://lexicon.ugr.es/) for related projects.

The name refers to sketch grammars, which are series of generalized corpus queries in Sketch Engine (see their [bibliography](https://www.sketchengine.eu/bibliography-of-sketch-engine/)).

Questions, suggestions, and support are welcome.

## Citation

If you use SGEX, please [cite it](https://zenodo.org/record/6812334).
