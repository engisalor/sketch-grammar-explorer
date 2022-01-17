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

- get SGE
  - download the [latest release](https://github.com/engisalor/sketch-grammar-explorer/releases) or clone this repo
- get a [Sketch Engine API key](https://www.sketchengine.eu/documentation/api-documentation/)
- install dependencies:
  - current versions `pip install -r requirements.txt`
  - required `pip install numpy pandas requests pyyaml`
  - optional `pip install keyring openpyxl lxml`

**API credentials**

Sketch Engine credentials can be supplied in plaintext or using the `keyring` package. 

***Manually***

Either add your username and API key to `data/config.yml`, or just add your username and execute the `keyring` command below to have your OS manage your key. `data/.config.yml` can be used instead to keep credentials untracked by git.

```python
import keyring

# to add credentials
keyring.set_password("Sketch Grammar Explorer","<username>", "<api_key>")

# to delete credentials later
keyring.delete_password("Sketch Grammar Explorer", "<username>")
```

***Automated***

Optionally, run `config.credentials()` to automate the process.

## Making API calls

To get started using example calls, run `config.examples()` to generate basic input files in `calls/`. Then run `Call()` with a path to an input file. Retrieved API data is stored in a folder of the same name.

``` python
import sge

sge.config.examples()
job = sge.Call("calls/freqs.yml")
```

**Options**

**`input`** a dictionary or a path to a YAML/JSON file containing API calls
  - if a dict, requires `dest="<destination folder>"`

**`dry_run`** make a `Call` object that can be inspected prior to executing requests
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
| collx     | -   | -   | yes  | -    | -   |
| freqs     | yes | yes | yes  | yes  | yes |
| wsketch   | -   | -   | yes  | yes  | -   |
| view      | -   | -   | yes  | -    | -   |

### Input files

**SGE call structure**

One or more calls can be executed by creating an input file readable by SGE that contains API calls in the form dictionaries of parameters. 

- input files require a `"type"` key indicating what kind of call it is (`"freqs"`)
- the key of each call serves as a call-id (`"call0"`)
- each call has a dictionary of API parameters in `"call"` 
- calls can optionally contain metadata in other key:value pairs
  
The call below queries the lemma "rock" in the [EcoLexicon English Corpus](https://www.sketchengine.eu/ecolexicon-corpus/) and retrieves frequencies by domain text type.

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

If `skip=True`, calls won't be repeated when identical data of the same file type already exists. Repeats are identified using hashes of `call` dictionaries (not metadata). If the contents of `"call"` change at all, they are considered unique calls.

The order of parameters is ignored for repeat identification. These are considered identical:

```yml
    q:
    corpname: preloaded/ecolexicon_en
    - alemma,"rock"

    corpname: preloaded/ecolexicon_en
    q:
    - alemma,"rock"
```

Repeats are not detected across input files. Queries from `calls1.yml` and `calls2.yml` are stored in their respective data folders and are treated as independent samples.

### Notes

**Modifying saved data**

Copy saved data to a different folder before making modifications. SGE doesn't detect file changes and will overwrite folder contents if `clear=True`.

**Working with different call types**

Each call type, `freqs` (frequencies), `view` (concordance), `wsketch` (word sketch), etc., has its own parameters and requirements: parameters are **not interchangeable** between call types but do share similarities.

**Too many requests**

Sketch Engine monitors API activity and will block excessive calls or other activity outside of their [Fair Use Policy](https://www.sketchengine.eu/fair-use-policy/). While learning the API, test calls selectively, slowly, and avoiding repeated identical calls.

**API usage**

To learn more about the API, it's helpful to inspect network activity while making queries in Sketch Engine with a web browser (using Developer Tools). Importantly, Sketch Engine has internal API methods that only function in web browsers, so merely copy-pasting certain methods into SGE won't necessarily work. Sketch Engine's API is also actively developed syntax/functionalities may change.

**Double-checking accuracy**

Before relying heavily on the API, it's a good idea to practice trying the same queries in a web browser and via API to make sure the results are identical, especially for an important data sample.

**Hashing for corpus linguists**

Hash functions are essential for software, but they can benefit linguists too. Using the hashes of corpus queries improves traceability, replicability, and quality control. While taking the hash of a simple, routine query may seem overkill, consider the many settings Sketch Engine has and the ways that errors can be silently introduced. When running hundreds of queries, the impact of a single change is hard to ignore.

Hashes are used in SGE to help users instantly recognize if two queries differ, however simple or complex. Generally speaking, if the corpus's content has not changed, two identical hashes should guarantee the same result. When using CQL rules that look more like paragraphs than phrases, hashes make it easy to notice if just one apostrophe has been misplaced. This is equally true of parameters, like if the search is changed from `lemma_lc` to `lemma`. Sometimes they simply aren't relevant, but users are encouraged to rely on hashes as part of an accountable corpus linguistics workflow.

## Tools

SGE will offer more features to automate repetitive tasks and procedures for certain methodologies. Feel free to suggest features.

**`convert_grammar()`** converts a sketch grammar into SGE-formatted queries (requires modifications depending on input)

**`Parse()`** parses and returns/saves a JSON/YAML file or dict of API calls
- `dest="<filepath>"` saves object to file in given format 
  - (can be used to convert between file formats)

## About

SGE has been developed to meet research needs at the University of Granada (Spain) Translation and Interpreting Department. Specifically, it is meant to support the computational linguistics techniques that feed the [EcoLexicon](https://lexicon.ugr.es/) terminological knowledge base (see the articles [here](https://aclanthology.org/W16-4709/) and [here](https://arxiv.org/pdf/1804.05294.pdf) for an introduction).

The name refers to sketch grammars, which are series of generalized corpus queries in Sketch Engine that are useful for studying terminology and other lexical items (see their [bibliography](https://www.sketchengine.eu/bibliography-of-sketch-engine/)).

Questions, suggestions, and support are welcome.

## Citation

If you use SGE, please [cite it](CITATION.cff).