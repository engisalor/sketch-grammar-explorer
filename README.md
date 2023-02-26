# Sketch Grammar Explorer

[![PyPI Latest Release](https://img.shields.io/pypi/v/sgex.svg)](https://pypi.org/project/sgex/)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.6812334.svg)](https://doi.org/10.5281/zenodo.6812334)
[![Package Status](https://img.shields.io/pypi/status/sgex.svg)](https://pypi.org/project/sgex/)
[![License](https://img.shields.io/pypi/l/sgex.svg)](https://github.com/pandas-dev/sgex/blob/main/LICENSE)

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
    - [Creating call objects: `sgex.call.type`](#creating-call-objects-sgexcalltype)
    - [Assembling CQL rules: `sgex.call.query`](#assembling-cql-rules-sgexcallquery)
    - [Managing calls: `sgex.call.call`](#managing-calls-sgexcallcall)
    - [Packaging and sending calls: `sgex.call.package`](#packaging-and-sending-calls-sgexcallpackage)
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

SGEX `0.6.0` is a complete redesign of the package and its previous functions may be deprecated. `0.5.5` is the last version before the switch. Its documentation has [moved](https://github.com/engisalor/sketch-grammar-explorer/blob/main/README_deprecated.md) and import paths have changed.

## Setup

Install SGEX with `pip install sgex`

Dependencies:
- required: `pandas pyyaml requests requests-cache`
- optional: `keyring openpyxl defusedxml`

Contributors also need `pre-commit`

## TL;DR

An abbreviated example of SGEX usage.

```python
from sgex.config import default
from sgex.call.type import Freqs
from sgex.call.package import Package

# add API credentials to the server configuration
config = {"ske": {**default["ske"], **{"username": "J. Doe", "api_key": "1234"}}}

# define API calls
calls = [
    # the first freqs call is complete (has all the needed parameters)
    Freqs({
        "format": "csv",
        "q": 'alemma,"eat"',
        "corpname": "preloaded/susanne",
        "fcrit": "doc.file 0",
        }),
    # successive freqs calls will reuse previous parameters
    Freqs({"q": 'alemma,"sleep"'})]

# package calls
package = Package(calls, "ske", config)

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

After trying out this basic example, see other sections on more advanced usage.

### 1. Setting a configuration dictionary

There are several ways to supply configuration settings to SGEX. This example modifies the default settings to show what each element means.

First, get a Sketch Engine API key [with these instructions](https://www.sketchengine.eu/documentation/api-documentation/#toggle-id-1) and review its API documentation to get familiarized.

```python
from sgex.config import default

# print default configuration settings
print(default)
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
default["ske"]["username"] = "J. Doe"
default["ske"]["api_key"] = "1234"
```

### 2. Making a `corp_info` API call

Each type of API call has its own Python class (`CorpInfo`), which is a child of the generic `Call` class. To make API calls, start by creating `Call` objects.

Calls are added to a `Package` class, which prepares requests and manages their execution. A `Package` can be inspected to make sure everything looks good before sending calls. Packages also expose other settings for more advanced usage.

```python
from sgex.call.type import CorpInfo
from sgex.call.package import Package

# indicate which server to use
server = "ske"

# define a call
call = CorpInfo({"corpname": "preloaded/susanne"})

# package the call
package = Package(call, server, default)

# inspect the package details
print(package.calls)
[CORP_INFO(723a010e) {'api_key': '1234', 'username': 'J. Doe', 'corpname': 'preloaded/susanne'}]

print(package.calls[0].request)
<Request [GET]>

# send the request
package.send_requests()
```

After the API call is successfully made it gets cached locally. Running `package.send_requests()` again retrieves data from the cache instead of making an external API call. Cache `session` settings are customizable: see the [requests-cache](https://requests-cache.readthedocs.io/) package for details.

### 3. Parsing results to a DataFrame

Cached API responses have JSON content by default. Other formats can be downloaded by adding `"format": "xml"` or similar to `Call` parameters. Available formats are`["json", "xml", "xls", "csv", "txt"]`). The availability of a format depends on the API call type (`freqs`, `view`, etc.) and the server being used. Only JSON is universally available; many combinations aren't allowed.

The `sgex.parse` package has several modules for manipulating data based on call type and format. More will be added over time for at least some common tasks.

The example below takes `corp_info` JSON content and converts it into a DataFrame.

```python
from sgex.parse.corp_info import sizes_json

# get the call response
response = package.responses[0]

# inspect the response
print(response.url)
'https://api.sketchengine.eu/bonito/run.cgi/corp_info?corpname=preloaded/susanne'

print(response.json())
{'wposlist': [['adjective', 'JJ.*'], ['adverb', 'RR.*'], ['conjuction', 'CC.*'], ['determiner', 'AT.*'], ... }

# (credentials are scrubbed from response content, URLs and JSON data)

# parse the response content with a `sgex.parse.corp_info` method
df = sizes_json(response)

# print the parsed content
print(df)
  structure    size
0     token  150426
1      word  128998
2       doc     149
...
```

After making a basic API call, look through more advanced options to develop your own workflow.

## Package structure

### Configuration: `sgex.config`

Configuration dictionaries can be passed to SGEX in several formats.

- a dictionary (see ``sgex.config.default``)
- a filepath to a JSON/YAML configuration file (``config.yml``)
- the name of a JSON-formatted environment variable (``SGEX_CONFIG_JSON``)
- a JSON-formatted string (``"{<JSON content>}"``)

The `sgex.config.load` function manages the parsing of these formats. If multiple source types exist, priority is given in this order: dict, json env variable, filepath, json str.

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

Configuration dictionaries can contain as many servers as needed in addition to the defaults `"ske"` and `"noske"`. [NoSketch Engine Docker](https://github.com/ELTE-DH/NoSketch-Engine-Docker) is a good place to start working with local servers.

### Exporting content: `sgex.io`

This module contains functions to load and save data. The easiest way to export data from `Response` objects is to use the `sgex.io.export_content` function.

```python
from sgex.io import export_content

# get response from package
response = package.responses[0]

# export it
export_content(response, "my-filename")
```

The `export_content` function will create `"my filename.<format>"` based on the `Response` object's content. If an error is raised when trying to export data, check ``response.content`` for any internal SkE errors and try making the same API call with ``"format": "json"``.

### Creating call objects: `sgex.call.type`

This module contains the classes for calls. `Call` is the base class inherited by others. `Call` contains a basic validation function to make sure improperly created calls are identified before requests get sent.

Each call type consists of a type, parameters, and required parameters. The example below shows the required parameters for several call types.

```python
from sgex.call import type as t

print(t.Freqs({}).required)
{'fcrit', 'q', 'corpname'}

print(t.Wordlist({}).required)
{'wltype', 'wlattr', 'corpname'}

print(t.View({}).required)
{'q', 'corpname'}
```

**Programmatically generating call lists**

Call classes can be used to programmatically generate many calls. The example below makes several `freqs` calls using list iteration. While this is convenient, to help reduce network traffic, be watchful for when multiple calls could be combined.

```python
from sgex.call.type import Freqs

# define queries
queries = ["apple", "banana", "peach", "strawberry", "blueberry"]

# make call list using iteration
calls = [
  Freqs({
    "q": f'alemma,"{q}"',
    "corpname": "<my corpus>",
    "fcrit": "doc.id 0",
    }) for q in queries]

# print results
print(calls)
[FREQS(*) {'q': 'alemma,"apple"', 'corpname': '<my corpus>', 'fcrit': 'doc.id 0'},
FREQS(*) {'q': 'alemma,"banana"', 'corpname': '<my corpus>', 'fcrit': 'doc.id 0'},
...

# the missing key in `FREQS(*)` isn't computed until calls get packaged
```

### Assembling CQL rules: `sgex.call.query`

This module has functions for simplifying the generation of [Corpus Query Language](https://www.sketchengine.eu/documentation/corpus-querying/) rules. Some calls don't need this feature, e.g., `'alemma,"peach"'`, but others might benefit.

`simple_query()` simulates the "Simple Query" feature in Sketch Engine. Words or phrases can be supplied as the string and the function outputs a CQL representation.

Following Sketch Engine's Simple Query, this function includes a few wildcards to make rules more flexible. Behavior may not be identical for complex patterns, though, so compare content retrieved via API and the standard user interface to verify desired results.

- Question marks `?` for any single character
- Asterisks `*` for any token or string of characters
- Double hyphens `--` for flexible hyphenation (with hyphen, without hyphen, no space in between)

```python
from sgex.call.query import simple_query

# example with hyphen
print(simple_query("flour-based recipe"))
'q( [lc="flour-based" | lemma_lc="flour-based"] | [lc="flour" | lemma_lc="flour"] [lc="-" | lemma_lc="-"] [lc="based" | lemma_lc="based"] )[lc="recipe" | lemma_lc="recipe"]'

# example with double hyphen and asterisk token
print(simple_query("flour--based *"))
'q( [lc="flourbased" | lemma_lc="flourbased"] | [lc="flour" | lemma_lc="flour"] [lc="based" | lemma_lc="based"] | [lc="flour-based" | lemma_lc="flour-based"] | [lc="flour" | lemma_lc="flour"] [lc="-" | lemma_lc="-"] [lc="based" | lemma_lc="based"] )[lc=".*" | lemma_lc=".*"]'
```

### Managing calls: `sgex.call.call`

This module has functions for preparing lists of `Call` objects. In general, accessing it directly isn't necessary, since `Package` initialization handles the below features.

**Recycling parameters**

`propagate()`, recycles parameters across calls of the same type. Call parameters are reused unless defined explicitly in every call. For example, the job below contains three similar `freqs` calls. Instead of writing out every parameter for each, only the first call is complete. The proceeding calls only contain new parameters to define.

```python
calls = [
    # the first call in a list always needs to be complete
    Freqs({
        "format": "csv",
        "q": 'alemma,"rock"',
        "corpname": "preloaded/susanne",
        "fcrit": "doc.file 0",
        }),
    # the next two freqs calls will recycle previous parameters
    Freqs({"q": 'alemma,"stone"'}),
    Freqs({"q": 'alemma,"pebble"'}),
    Wordlist({"corpname": "preloaded/susanne"}),
    # this freqs call will be incomplete!
    Freqs({"q": 'alemma,"sand"'})]
```

If a different call type appears, like `Wordlist`, parameter recycling stops. Adding another `freqs` call at the end of the list would require supplying a complete set of parameters again.

**Normalizing Call dictionaries**

`normalize_dt` standardizes API call formatting. This helps avoid making duplicate calls when parameters are functionally equivalent. It's most apparent with parameters that take lists. These two `fcrit` values return the same results regardless of list order.

- `{"fcrit": ["doc.genre 0", "doc.editor 0", "doc.year 0"]}`
- `{"fcrit": ["doc.editor 0", "doc.year 0", "doc.genre 0"]}`

Normalization is limited, however, so it's best to follow consistent formatting when making calls. The two queries below are the same but the extra space doesn't get normalized (yet); this usually applies to string values.

- `{"q": 'alemma,"stone"'}`
- `{"q": 'alemma, "stone"'}`

**Cached content key creation**

To manage call caching with `requests-cache`, sorted dictionaries of normalized call parameters get passed to a custom hashing function (`create_key_from_params`). The keys assigned to calls can be accessed as shown below. Keys correspond to cache filenames, table rows, etc., depending on the backend.

```python
# show part of key for each call
print(package.calls)
[FREQS(f9584ba5) {'q': 'alemma, "eat"', 'corpname': 'susanne', 'fcrit': 'doc.file 0'},
FREQS(fe922380) {'q': 'alemma,"eat"', 'fcrit': 'doc.file 0', 'corpname': 'susanne'}]

# show full key for one call
print(package.calls[0].key)
'f9584ba5e14aebc0'
```

### Packaging and sending calls: `sgex.call.package`

This module has the `Package` class, which manages the different aspects of making and executing API calls.

**Methods for sending calls**

- `Package.send_requests()` executes a list of calls sequentially, following throttling instructions in `config["<server>"]["<wait>"]`, if provided
- `Package.send_async_requests()` executes a list of calls asynchronously, if `config["<server>"]["asynchronous"] = True`

Both of these methods have some error handling to prevent repeating calls if something is misconfigured, but test large jobs beforehand nonetheless to avoid issues.

**Server wait times**

Servers may require waiting between calls. SGEX manages waiting for the Sketch Engine server following their [Fair Use Policy](https://www.sketchengine.eu/fair-use-policy/) guidelines. If a custom server requires waiting, this can be enabled by adding a `wait` entry in the configuration, like below:

```yml
ske:         # server name
  wait:      # wait dictionary (in seconds)
  0: 1       # wait = 0 for 1 call
  2: 99      # wait = 2 for 2-99 calls
  5: 899     # wait = 5 for 100-899 calls
  45: null   # wait = 45 for 900 or more calls
```

Call throttling is implemented as a `Request.response` hook, meaning that waiting is only applied for calls that haven't been cached yet.

**Asynchronous calling**

For local servers, asynchronous calling can increase performance substantially. By default, the number of threads adjusts according to the number of CPUs available (see `max_workers` for [concurrent.futures](https://docs.python.org/3/library/concurrent.futures.html#concurrent.futures.ThreadPoolExecutor)).

SGEX can make hundreds of thousand of calls to a local server in a single job. This is advantageous for conducting large linguistic analyses, but watch out for unexpected behaviors caused by high loads.

**Customizing Package settings**

The `requests-cache` session can be modified to use different backends (Redis, SQLite, filesystem, etc.), as well as other features. This is an example of Package attributes:

```python
Package.calls: list # list of calls
Package.server: str # server to call
Package.halt: bool  # whether to stop a job on error
Package.errors: set # errors encountered
Package.max_workers: int # threads for asynchronous calls
Package.responses: list # call responses
Package.max_responses: int # max items to be stored in `Package.responses` (for large jobs)
Package.session_params: dict( # parameters for the `request-cache` session
    cache_name="data",
    serializer="json",
    backend="filesystem",
    ignored_parameters=ignored_parameters,
    key_fn=call.create_key_from_params,
)
Package.config: dict # server configuration
Package.session: requests_cache.CachedSession # session object
```

Settings can be changed by adding additional `kwargs` during instantiation. Print `package.__dict__` before making calls to see all options at once.

### Running complex tasks: `sgex.call.job`

This module has classes that combine multiple API calls, parsing methods, etc., to execute larger jobs. It currently has two types of jobs, both of which parse JSON data. Since JSON responses have the most detailed data and work for all call types, this is often more useful than fetching CSV data with a simple table. It does, however, require more legwork to parse the data.

**Text type analysis**

`job.TTypeAnalysis` automates the steps for generating a DataFrame describing the corpus's composition.

```python
from sgex.call.job import TTypeAnalysis

# prepare the job
ttypes = TTypeAnalysis("susanne", <server>, <config>)

# run the job
ttypes.run()

# view the results
print(ttypes.df.head(5))
    str  frq  relfreq  attribute
0  ital  263  1748.37  font.type
1  bold   38   252.62  font.type
2   maj  182  1209.90  head.type
3   min   77   511.88  head.type
4   A19   12    79.77   doc.file
```

**Simple frequency query**

`job.SimpleFreqsQuery` automates making a `freqs` call with Simple Query syntax and processing JSON data into a DataFrame.

```python
from sgex.call.job import SimpleFreqsQuery

# prepare the job
query = SimpleFreqsQuery("sleep", "susanne", "noske", ".config.yml")

# run the job
query.run()

# view the results (each row is a corpus attribute/text type)
print(query.df.head(5))
   frq         rel        reltt  ...  total_fpm total_size fmaxitems
0   24     0.00000     0.000000  ...     159.55         24       500
1   24     0.00000     0.000000  ...     159.55         24       500
2    9  2245.61107  3582.802548  ...     159.55         24       500
3    6  1624.47084  2591.792657  ...     159.55         24       500
4    3   748.53702  1194.267516  ...     159.55         24       500

[5 rows x 12 columns]
```

Reviewing the code for these classes may be helpful when designing your own multi-step tasks. They are broken into methods that execute each step/API call type and then process the data. A `.run()` method is defined to bring everything together.

### Parsing data: `sgex.parse`

This subpackage has modules for parsing each API call type's data. `sgex.parse.freqs`, for example, has functions for working with `freqs` data. Functions that work with a specific format are suffixed to make it clear what they can be used. For example, `sgex.parse.freqs.freqs_json` is useful to parse JSON data only, but it relies on other functions, like `sgex.parse.freqs.clean_heads`, which works on DataFrames.

Since many types of call and format options are possible, the `parse` module isn't likely to offer methods for every circumstance. JSON is decidedly the focus, though parsing its sometimes complex structures can require more effort.

## API usage notes

**Too many requests**

Sketch Engine blocks API activity outside of their FUP. While learning the API, test calls selectively, slowly, and avoid repeated identical calls.

**API behavior**

To learn more about the API, it's helpful to inspect network activity while using the Sketch Engine interface. Importantly, Sketch Engine has some internal API methods that won't work if copy-pasted into SGEX calls.

**Double-checking accuracy**

Before relying heavily on the API, it's a good idea to practice trying the same queries both in a web browser and via API to make sure the results are identical.

## Security

Some considerations for using SGEX.

### API credentials

Response data can include credentials in several locations and should be removed before storing or sharing. SGEX mitigates the exposure of credentials with the `sgex.config.ignored_parameters` list, which `requests-cache` uses to strip secret parameters from URLs/session data. A custom hook has also been added to redact credentials from JSON response data before it gets cached.

### Data storage

Data can be stored more securely by using a custom serializer with `requests-cache`, as in the example below, which encrypts data on the fly. When storing unencrypted `pickle` data, they recommend using the [safe_pickle_serializer](https://requests-cache.readthedocs.io/en/stable/user_guide/security.html).

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
