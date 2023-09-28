# Sketch Grammar Explorer

[![PyPI Latest Release](https://img.shields.io/pypi/v/sgex.svg)](https://pypi.org/project/sgex/)
[![PyPI - Python Versions](https://img.shields.io/pypi/pyversions/sgex)](https://pypi.org/project/sgex)
[![Package Status](https://img.shields.io/pypi/status/sgex.svg)](https://pypi.org/project/sgex/)
[![License](https://img.shields.io/pypi/l/sgex.svg)](https://github.com/pandas-dev/sgex/blob/main/LICENSE)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.6812334.svg)](https://doi.org/10.5281/zenodo.6812334)

## Introduction

Sketch Grammar Explorer (SGEX) is a Python package for using the API of [Sketch Engine](https://www.sketchengine.eu/), a language corpus management software useful for many types of linguistic research. The package's goal is developing a flexible scaffold for any kind of programmatic work with Sketch Engine and [NoSketch Engine](https://nlp.fi.muni.cz/trac/noske).

**NOTE**

SGEX `0.7.0+` is another redesign of the package that greatly simplifies the code and makes better features possible. SkE has updated their API and these changes are meant to facilitate easy adoption. The previous `0.6.x` versions are deprecated and unavailable in the current release: don't upgrade until downstream code is adapted.

## Installation

Clone SGEX or install it with `pip install sgex` (its main dependencies are `pandas pyyaml aiohttp aiofiles`).

Get a [Sketch Engine API key](https://www.sketchengine.eu/documentation/api-documentation/#toggle-id-1).
Be sure to use SkE's documentation and refer to their schema:

`wget https://www.sketchengine.eu/apidoc/openapi.yaml -O .openapi.yaml`

## Usage

Documentation is being rewritten: see the [GitHub repo](https://github.com/engisalor/sketch-grammar-explorer) for the latest.

## About

SGEX has been developed to meet research needs at the University of Granada Translation and Interpreting Department. See the [LexiCon research group](http://lexicon.ugr.es/) for related projects.

The name refers to sketch grammars, which are series of generalized corpus queries in Sketch Engine (see their [bibliography](https://www.sketchengine.eu/bibliography-of-sketch-engine/)).

Questions, suggestions and support are welcome.

## Citation

If you use SGEX, please cite it:

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

See its [Zenodo DOI](https://zenodo.org/record/6812334) for citing the software itself.
