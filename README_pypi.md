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

See the [code repository](https://github.com/engisalor/sketch-grammar-explorer) for full documentation.
