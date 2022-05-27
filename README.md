# Sketch Grammar Explorer

- [Sketch Grammar Explorer](#sketch-grammar-explorer)
  - [Introduction](#introduction)
  - [Setup](#setup)
  - [Making API calls](#making-api-calls)
    - [Input files](#input-files)
    - [Features](#features)
    - [Notes](#notes)
  - [About](#about)
  - [Citation](#citation)

## Introduction

Sketch Grammar Explorer (SGEX) is a Python package for using the [Sketch Engine](https://www.sketchengine.eu/) API. The goal is to develop a flexible scaffold for any kind of programmatic work with Sketch Engine and [NoSketch Engine](https://nlp.fi.muni.cz/trac/noske).

## Setup

Built with Python 3.10 and tested on 3.7.

**Installation**

- get a [Sketch Engine API key](https://www.sketchengine.eu/documentation/api-documentation/) (if using their server)

Install with pip:

- `pip install sgex`

Or manual install:

- clone this repo
- install dependencies:
  - current versions `pip install -r requirements.txt`
  - required `pip install pandas requests pyyaml`
  - optional `pip install keyring openpyxl lxml`

**API credentials**

Run `sgex.config.credentials()` to automate the creation of a `config.yml` file in the project directory. Follow the prompts to store an API key in plaintext or with the `keyring` package. The config file can also be created manually (see [config example](/config.yml)).

Credentials consist of servers, usernames, and API keys. To add more servers, just modify `config.yml`. If a server doesn't require credentials, use a non-empty string, e.g., `'null'` for both `username` and `api_key`. If necessary, a keyring entry can be modified directly as shown below.

```python
import keyring

# to add credentials
keyring.set_password("<server>","<username>", "<api_key>")

# to delete credentials later
keyring.delete_password("<server>", "<username>")
```

## Making API calls

To get started using example calls, run `sgex.config.examples()` to generate an input file in `calls/`. Then run `sgex.Call()` with a path to an input file. Retrieved API data is stored in sqlite databases in `data/`. The default database is `sgex.db`; new databases are created when other filenames are supplied.

API responses can also be saved directly to `data/raw/` in supported file types (JSON, CSV, XLSX, TXT, XML) using `output="csv"`, etc. This always overwrites prexisting data. 

JSON is the universal format and the only one with error reporting. Supported formats generally depend on the shape of the data: e.g., `view` requires JSON and `freqs` accepts all file types. NoSketch Engine servers may not output XLSX.

``` python
import sgex

sgex.config.examples()
job = sgex.Call("calls/examples.yml")
```

**Options**

`input` a dictionary or path to a YAML/JSON file containing API calls

`output` save to sqlite (default `sgex.db`) or files: `json`, `csv`, `xlsx`, `xml`, `txt`

`dry_run` (`False`)

`skip` skip calls when a hash of the same call parameters exists in sqlite (`True`)

`clear` remove existing data before calls (sqlite table or `data/raw/`) (`False`)

`server` (`"https://api.sketchengine.eu/bonito/run.cgi"`)

`wait` `None` for default (`False` if localhost, otherwise `True`) - override with boolean

`threads` for asynchronous calling (`None` for default, otherwise an integer)

`progress` show progress (`True`)

`loglevel` (`"info"`) see `.sgex.log`

### Input files

**SGEX call structure**

One or more calls can be executed by creating an input file readable by SGEX that contains API calls in the form dictionaries of parameters.

- the key of each call serves as an id (`"call0"`)
- call types (frequency, concordance, etc.) are defined with `"type"`
- each call has a dictionary of API parameters in `"call"`
- calls can optionally contain metadata in `"meta"`
- `"keep"` can be used to save only a portion of response data (JSON only)

The call below queries the lemma "rock" in the [EcoLexicon English Corpus](https://www.sketchengine.eu/ecolexicon-corpus/) and retrieves frequencies by several text types.

**YAML**

Queries can be copied directly from YAML files into Sketch Engine's browser application without adding/removing escape characters.

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

### Features

**Recycling parameters**

Parameters are reused unless defined explicitly in every call. For example, the job below contains three similar calls. Instead of writing out every parameter for each, only the first call is complete. The proceeding calls only contain new parameters to define.

Parameters can be passed through sequential calls of the same type. If `type` appears in a new call, nothing is reused. When parameters are part of a dictionary, its items are passed individually, whereas strings, lists, and other data types are replaced.

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

If `skip=True`, a call won't be repeated when an identical call has already been made in a sqlite database. Repeats are identified using hashes of call dictionaries. If the contents of `"call"` change at all (even one character), they are considered unique calls. If `skip=False`, existing data is replaced when a new call has the same hash.

**Asynchronous calling**

Asynchronous calling is enabled when using a local server, which can increase performance substantially. By default the number of threads adjusts according to the number of CPUs available (see `max_workers` for [concurrent.futures](https://docs.python.org/3/library/concurrent.futures.html#concurrent.futures.ThreadPoolExecutor)). In this mode a job must finish before responses are saved.

**Discarding unwanted data with `keep`**

SGEX saves the entire response for each API call by default. Instead, `keep` can be used to specify what JSON data to save. For example, if `keep="concsize"` is set for `freqs` calls, only the absolute frequency is kept and the rest of the response is discarded. `keep` only works for top-level items, not nested data.

### Notes

**Working with different call types**

Each call type, `freqs` (frequencies), `view` (concordance), `wsketch` (word sketch), etc., has its own parameters and requirements: parameters are **not interchangeable** between call types but do share similarities.

**Too many requests**

Sketch Engine monitors API activity and will block excessive calls or other activity outside of their [Fair Use Policy](https://www.sketchengine.eu/fair-use-policy/). While learning the API, test calls selectively, slowly, and avoid repeated identical calls.

**API usage**

To learn more about the API, it's helpful to inspect network activity while making queries in Sketch Engine with a web browser (using Developer Tools). Importantly, Sketch Engine has internal API methods that only function in web browsers, so merely copy-pasting certain methods into SGEX won't necessarily work. Sketch Engine's API is also actively developed and syntax/functionalities may also change.

**Double-checking accuracy**

Before relying heavily on the API, it's a good idea to practice trying the same queries both in a web browser and via API to make sure the results are identical.

**Saving and converting calls** 

`Parse()` is used to read API calls, but it can save call dictionaries and convert them to/from JSON and YAML files. Use `dest="<filepath>"` to save an object to file with the desired format.

## About

SGEX has been developed to meet research needs at the University of Granada (Spain) Translation and Interpreting Department, in part to support the computational linguistics techniques that feed the [EcoLexicon](https://lexicon.ugr.es/) terminological knowledge base (see the articles [here](https://aclanthology.org/W16-4709/) and [here](https://arxiv.org/pdf/1804.05294.pdf) for an introduction).

The name refers to sketch grammars, which are series of generalized corpus queries in Sketch Engine that are useful for studying terminology and other lexical items (see their [bibliography](https://www.sketchengine.eu/bibliography-of-sketch-engine/)).

Questions, suggestions, and support are welcome.

## Citation

If you use SGEX, please [cite it](CITATION.cff).