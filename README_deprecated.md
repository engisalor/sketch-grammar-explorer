# Sketch Grammar Explorer

[![PyPI Latest Release](https://img.shields.io/pypi/v/sgex.svg)](https://pypi.org/project/sgex/)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.6812334.svg)](https://doi.org/10.5281/zenodo.6812334)
[![Package Status](https://img.shields.io/pypi/status/sgex.svg)](https://pypi.org/project/sgex/)
[![License](https://img.shields.io/pypi/l/sgex.svg)](https://github.com/pandas-dev/sgex/blob/main/LICENSE)

- [Sketch Grammar Explorer](#sketch-grammar-explorer)
  - [Introduction](#introduction)
  - [Setup](#setup)
  - [Making API calls](#making-api-calls)
    - [Saving results](#saving-results)
    - [Input files](#input-files)
  - [Features](#features)
  - [Notes](#notes)
  - [About](#about)
  - [Citation](#citation)

## Introduction

Sketch Grammar Explorer (SGEX) is a Python package for using the [Sketch Engine](https://www.sketchengine.eu/) API. The goal is to develop a flexible scaffold for any kind of programmatic work with Sketch Engine and [NoSketch Engine](https://nlp.fi.muni.cz/trac/noske).

**NOTE**

SGEX is being redesigned and the below functionalities will be deprecated in upcoming versions. See the new `_call` module for current development.

## Setup

Built with Python 3.10. (Compatibility with 3.7 is no longer being tested.)

**Installation**

- get a [Sketch Engine API key](https://www.sketchengine.eu/documentation/api-documentation/) (if using their server)

Install SGEX with pip:

- `pip install sgex`

Or manually:

- clone the GitHub repo
- install dependencies:
  - current versions `pip install -r requirements.txt`
  - required `pip install requests pyyaml`
  - optional `pip install keyring pandas openpyxl lxml`

**API credentials**

To configure SGEX, either run the code below or manually copy the example [config file](https://github.com/engisalor/sketch-grammar-explorer/blob/dev/config.yml) to your project directory.

```python
import sgex
sgex.Call(sgex.call_examples) # SGEX generates a config file if none found
```

The config file contains API credentials and other settings for servers. Before making calls to a server, set up your credentials:

- if a server requires credentials, add a username and API key
- API keys can also be managed with the `keyring` package
  - to add an entry: `keyring.set_password("<server>","<username>","<api_key>")`
  - in the config file, include the username but leave the API key as `null`

The default config file includes two servers: for Sketch Engine and a local NoSketch Engine installation. Add more as needed.

## Making API calls

To get started making calls, generate an example input file and execute the job:

```python
import sgex

sgex.parse(sgex.call_examples, "examples.yml") # modify examples.yml as desired
sgex.Call("examples.yml", loglevel="info")
```

SGEX parses calls from the input file, makes requests to the server, and stores results in `data/sgex.db`. Next, make your own input files and experiment with other features.

**Options**

`input` a dictionary or path to a YAML/JSON file containing API calls

`output` save to sqlite (default `sgex.db`) or individual files: `json`, `csv`, `xlsx`, `xml`, `txt`

`dry_run` (`False`)

`skip` skip calls when a hash of the same parameters already exists in sqlite (`True`)

`clear` remove preexisting data (`False`)

`server` select a server from `config.yml` (`"ske"`)

`threads` for asynchronous calling (`None` for default, otherwise an integer <= 32)

`halt` (`True`) abort calls on HTTP response error

`loglevel` (`"warning"`) outputs to `.sgex.log`

### Saving results

Retrieved API data is stored in sqlite databases in `data/`. The default database is `sgex.db`; new databases are created when other filenames are supplied (always use the `.db` extension).

API responses can also be saved to `data/raw/` in supported file types (JSON, CSV, XLSX, TXT, XML) using `output="csv"`, etc. This will overwrite pre-existing data.

Support for output formats depends on the call type: e.g., `view` requires JSON and `freqs` accepts all file types. JSON is the only format that works for all call types. NoSketch Engine servers may not be compatible with some formats and call types (see [this comparison](https://www.sketchengine.eu/nosketch-engine/)).

### Input files

**SGEX call structure**

One or more calls can be executed by supplying a YAML or JSON input file that contains API calls in the form dictionaries of parameters.

- the key of each call serves as an id (`"call0"`)
- call types (frequency, concordance, etc.) are defined with `"type"`
- each call has a dictionary of API parameters in `"call"`
- calls can optionally contain custom metadata in `"meta"`
- `"keep"` can be used to save only a portion of response data (when `output="<filename>.db" or "json"`)

The call below queries the lemma "rock" in the [EcoLexicon English Corpus](https://www.sketchengine.eu/ecolexicon-corpus/) and retrieves frequencies by several text types.

**YAML**

YAML preserves CQL formatting and doesn't require extra character escaping:

```yml
call0:
  type: freqs
  meta:
    category1: tag1
  call:
    q:
    - alemma,"rock"
    corpname: preloaded/ecolexicon_en
    freq_sort: freq
    fcrit:
    - doc.domains 0
    - doc.genre 0
    - doc.editor 0
```

**JSON**

JSON requires consistent usage of double quotes and escape characters:

- interior double quotes escaped `"alemma,\"rock\""`, `"aword,\"it's\""`
- double-escaping for special characters: `"atag,1:\"N.*\" [word=\",|\\(\"]`

```json
{ "call0": {
    "type": "freqs",
    "meta": {
      "category1": "tag1"
    },
    "call":{
      "q": [
        "alemma,\"rock\""
      ],
      "corpname": "preloaded/ecolexicon_en",
      "freq_sort": "freq",
      "fcrit": [
        "doc.domains 0",
        "doc.genre 0",
        "doc.editor 0"]}}}
```

**Dictionary**

Rather than making an input file, calls can be supplied directly as a dictionary. This is convenient when generating or modifying calls programmatically.

## Features

**Recycling parameters**

Parameters are reused unless defined explicitly in every call. For example, the job below contains three similar calls. Instead of writing out every parameter for each, only the first call is complete. The proceeding calls only contain new parameters to define.

Parameters are passed sequentially through calls of the same type. If `type` appears in a new call, nothing is reused. When parameters are part of a dictionary, its items get passed individually. Strings and other data types are just replaced.

```yml
call0:
  type: freqs
  call:
    q:
    - alemma,"rock"
    corpname: preloaded/ecolexicon_en
    freq_sort: freq
    fcrit:
    - doc.domains 0

call1:
  call:
    q:
    - alemma,"stone"

call2:
  call:
    q:
    - alemma,"pebble"
```

**Skipping repeats**

If `skip=True`, a call won't be repeated when an identical call has already been made for a sqlite database. Repeats are identified using hashes of call dictionaries. If the contents of `"call"` change at all (even one character), they are considered unique calls. Being Python dictionaries, the order of call parameters doesn't matter. If `skip=False`, existing data is replaced when a new call has the same hash. Metadata does not affect hashes or call skipping.

**Asynchronous calling**

For local servers, asynchronous calling can increase performance substantially. Enable it by adding `asynchronous: True` to a server's details in `config.yml`. By default, the number of threads adjusts according to the number of CPUs available (see `max_workers` for [concurrent.futures](https://docs.python.org/3/library/concurrent.futures.html#concurrent.futures.ThreadPoolExecutor)).

**Discarding unwanted JSON data**

SGEX saves the entire response for each API call by default. Instead, `keep` can be used to specify what JSON data to save. For example, if `keep="concsize"` is set for `freqs` calls, only the absolute frequency is kept and the rest of the response is discarded. `keep` only works for top-level items, not nested data.

**Server wait times**

Servers may require waiting between calls. SGEX manages waiting for the Sketch Engine server using their [Fair Use Policy](https://www.sketchengine.eu/fair-use-policy/) guidelines. If a custom server requires waiting, this can be enabled by adding a `wait` entry in the config file, like below:

```yml
ske:         # server name
  wait:      # wait dictionary (in seconds)
  0: 1       # wait = 0 for 1 call
  2: 99      # wait = 2 for 2-99 calls
  5: 899     # wait = 5 for 100-899 calls
  45: null   # wait = 45 for 900 or more calls
```

## Notes

**Working with different call types**

Each call type, `freqs` (frequencies), `view` (concordance), `wsketch` (word sketch), etc., has its own parameters and requirements: parameters are **not interchangeable** between call types but do share similarities.

**Too many requests**

Sketch Engine will block API activity outside of their FUP. While learning the API, test calls selectively, slowly, and avoid repeated identical calls.

**API usage**

To learn more about the API, it's helpful to inspect network activity while using the Sketch Engine interface. Importantly, Sketch Engine has some internal API methods that won't work if copy-pasted into SGEX calls.

**Double-checking accuracy**

Before relying heavily on the API, it's a good idea to practice trying the same queries both in a web browser and via API to make sure the results are identical.

**Saving and converting input files**

`parse()` reads input files, but it can also save call dictionaries and convert them to/from JSON/YAML formats using `dest="<filepath>"`.

**Logging and error handling**

- a bad response stops jobs immediately if `halt=True`
- error information is saved when using sqlite
- `summary()` fetches job details from `Call` objects

Logging levels print the following information:

- `critical` - nothing
- `error` - TBD
- `warning` - each API/response error with its call id
- `info` - progress and job summary
- `debug` - everything

## About

SGEX has been developed to meet research needs at the University of Granada (Spain) Translation and Interpreting Department. See the [LexiCon research group](http://lexicon.ugr.es/) for related projects.

The name refers to sketch grammars, which are series of generalized corpus queries in Sketch Engine (see their [bibliography](https://www.sketchengine.eu/bibliography-of-sketch-engine/)).

Questions, suggestions, and support are welcome.

## Citation

If you use SGEX, please [cite it](https://zenodo.org/record/6812334).