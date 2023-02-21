# Sketch Grammar Explorer

[![PyPI Latest Release](https://img.shields.io/pypi/v/sgex.svg)](https://pypi.org/project/sgex/)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.6812334.svg)](https://doi.org/10.5281/zenodo.6812334)
[![Package Status](https://img.shields.io/pypi/status/sgex.svg)](https://pypi.org/project/sgex/)
[![License](https://img.shields.io/pypi/l/sgex.svg)](https://github.com/pandas-dev/sgex/blob/main/LICENSE)

- [Sketch Grammar Explorer](#sketch-grammar-explorer)
  - [Introduction](#introduction)
  - [Setup](#setup)
  - [About](#about)
  - [Citation](#citation)

## Introduction

Sketch Grammar Explorer (SGEX) is a Python package for using the [Sketch Engine](https://www.sketchengine.eu/) API. The goal is to develop a flexible scaffold for any kind of programmatic work with Sketch Engine and [NoSketch Engine](https://nlp.fi.muni.cz/trac/noske).

**NOTE**

SGEX is being redesigned and its previous structure will be deprecated in future versions. Version `0.5.5` still functions, but its documentation has been [moved](/README_deprecated.md). The current README will be updated progressively.

## Setup

Install SGEX with `pip install sgex`

Dependencies:
- required: `requests requests-cache pyyaml`
- optional: `keyring openpyxl defusedxml`

Developers also need `pre-commit`

## About

SGEX has been developed to meet research needs at the University of Granada (Spain) Translation and Interpreting Department. See the [LexiCon research group](http://lexicon.ugr.es/) for related projects.

The name refers to sketch grammars, which are series of generalized corpus queries in Sketch Engine (see their [bibliography](https://www.sketchengine.eu/bibliography-of-sketch-engine/)).

Questions, suggestions, and support are welcome.

## Citation

If you use SGEX, please [cite it](https://zenodo.org/record/6812334).
