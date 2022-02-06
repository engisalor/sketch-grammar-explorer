# Sketch Grammar Explorer

- [Sketch Grammar Explorer](#sketch-grammar-explorer)
  - [Introduction](#introduction)
  - [Setup](#setup)
  - [Making API calls](#making-api-calls)
    - [Output formats](#output-formats)
    - [Input files](#input-files)
    - [Features](#features)
    - [Notes](#notes)
  - [Tools](#tools)
  - [About](#about)
  - [Citation](#citation)

## Introduction

Sketch Grammar Explorer (SGE) is a Python package for using the [Sketch Engine API](https://www.sketchengine.eu/). This includes (or will include) modules for related data analysis tasks: preparing sets of API calls, munging data, generating spreadsheets, and visualization. The goal is to develop a flexible scaffold for any kind of programmatic work with Sketch Engine.

## Setup

Built with Python 3.10 and tested on 3.7.

**Installation**

- get a [Sketch Engine API key](https://www.sketchengine.eu/documentation/api-documentation/)

Install/update from GitHub with pip:

- `pip install --upgrade git+https://github.com/engisalor/sketch-grammar-explorer.git` 

Or manually:

- clone this repo and install dependencies:
  - current versions `pip install -r requirements.txt`
  - required `pip install numpy pandas requests pyyaml`
  - optional `pip install keyring openpyxl lxml`

**API credentials**

Run `config.credentials()` to automate the creation of a `config.yml` file in the project directory. Follow the prompts to store an API key in plaintext or with the `keyring` package. If necessary, the keyring entry can be modified directly as shown below.

```python
import keyring

# to add credentials
keyring.set_password("Sketch Grammar Explorer","<username>", "<api_key>")

# to delete credentials later
keyring.delete_password("Sketch Grammar Explorer", "<username>")
```

## Making API calls

To get started using example calls, run `config.examples()` to generate basic input files in the current working directory. Then run `Call()` with a path to an input file. Retrieved API data is stored in a folder of the same name.

``` python
import sge

sge.config.examples()
job = sge.Call("calls/freqs.yml")
```

**Options**

**`input`** a dictionary or a path to a YAML/JSON file containing API calls
  - if a dict, requires `dest="<destination folder>"`

**`dry_run`** make a `Call` object that can be inspected prior to executing requests (`False`)
  - with `job` as an instance of `Call`: 
  - `job` prints a summary
  - `job.print_calls()` prints 10 call details at a time
  - `job.calls` accesses all call details

**`skip`** skip calls if identical data already exists in the destination folder (`True`)
  - only compares files of the same format
  - note: close data files to ensure read access

**`clear`** remove existing data in destination folder before running current calls (`False`)

**`timestamp`** include a timestamp (`False`)

**`format`** specify output format (`"json"`)

- `"csv"`, `"txt"`, `"json"`, `"xlsx"`, or `"xml"` (see compatibilities table)
- `"json"` offers more detailed metadata and API error messages

**`any_format`** allow any combination of call types and formats (`False`)

**`asyn`** retrieve rough calculations, `"0"` (default) or `"1"`

### Output formats

SGE can save data in all formats provided by Sketch Engine, although only JSON is compatible with all call types. Known incompatibilities are blocked unless `any_format=True`.

**Compatible call types and file formats**
| call type | csv | txt | json | xlsx | xml |
|-----------|-----|-----|------|------|-----|
| collx     |     |     | +    |      |     |
| freqs     | +   | +   | +    | +    | +   |
| wordlist  | +   |     | +    | +    | +   |
| wsketch   |     |     | +    | +    |     |
| view      |     |     | +    |      |     |

### Input files

**SGE call structure**

One or more calls can be executed by creating an input file readable by SGE that contains API calls in the form dictionaries of parameters. 

- input files require a `"type"` key indicating what kind of call it is (`"freqs"`)
- the key of each call serves as a call-id (`"call0"`)
- each call has a dictionary of API parameters in `"call"` 
- calls can optionally contain metadata in other key:value pairs
  
The call below queries the lemma "rock" in the [EcoLexicon English Corpus](https://www.sketchengine.eu/ecolexicon-corpus/) and retrieves frequencies by several text types.

**YAML** 

YAML files (`.yml` or `.yaml`) allow queries to be copied directly into Sketch Engine's browser application.

```yml
type: freqs
call0:
  metadata:
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
{ "type": "freqs",
  "call0": {
    "metadata": {
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

Parameters are reused unless defined explicitly in every call. For example, the job below contains three similar calls. Instead of writing out every parameter for each, only the first call is complete. The proceeding calls only contain differing parameters (their queries). Other parameters (`corpname`, etc.), are passed from the first call successively to the rest.

```yml
type: freqs

call0:
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

If `skip=True`, calls won't be repeated when identical data of the same file type already exists. Repeats are identified using hashes of `call` dictionaries. If the contents of `"call"` change at all, they are considered unique calls.

Repeats are not detected across input files. Queries from `calls1.yml` and `calls2.yml` are stored in their respective data folders and are treated as independent samples.

### Notes

**Modifying saved data**

SGE doesn't track changes you make to downloaded data and will overwrite files if `skip=False` or `clear=True`. Be sure to use separate destination folders for different samples or copy samples to another location to prevent data loss. 

**Working with different call types**

Each call type, `freqs` (frequencies), `view` (concordance), `wsketch` (word sketch), etc., has its own parameters and requirements: parameters are **not interchangeable** between call types but do share similarities.

**Too many requests**

Sketch Engine monitors API activity and will block excessive calls or other activity outside of their [Fair Use Policy](https://www.sketchengine.eu/fair-use-policy/). While learning the API, test calls selectively, slowly, and avoiding repeated identical calls.

**API usage**

To learn more about the API, it's helpful to inspect network activity while making queries in Sketch Engine with a web browser (using Developer Tools). Importantly, Sketch Engine has internal API methods that only function in web browsers, so merely copy-pasting certain methods into SGE won't necessarily work. Sketch Engine's API is also actively developed and syntax/functionalities may also change.

**Double-checking accuracy**

Before relying heavily on the API, it's a good idea to practice trying the same queries both in a web browser and via API to make sure the results are identical.

## Tools

SGE will offer more features to automate repetitive tasks and procedures for certain methodologies. Feel free to suggest features.

**`convert_grammar()`** converts a sketch grammar into SGE-formatted queries (requires modifications depending on input)

**`Parse()`** parses and returns a dict of API calls or saves to a JSON/YAML file.
- `dest="<filepath>"` saves an object to file (can be used to convert between file formats)

## About

SGE has been developed to meet research needs at the University of Granada (Spain) Translation and Interpreting Department, in part to support the computational linguistics techniques that feed the [EcoLexicon](https://lexicon.ugr.es/) terminological knowledge base (see the articles [here](https://aclanthology.org/W16-4709/) and [here](https://arxiv.org/pdf/1804.05294.pdf) for an introduction).

The name refers to sketch grammars, which are series of generalized corpus queries in Sketch Engine that are useful for studying terminology and other lexical items (see their [bibliography](https://www.sketchengine.eu/bibliography-of-sketch-engine/)).

Questions, suggestions, and support are welcome.

## Citation

If you use SGE, please [cite it](CITATION.cff).