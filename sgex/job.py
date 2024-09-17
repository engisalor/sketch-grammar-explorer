#!/usr/bin/python3
# Copyright (c) 2022-2023 Loryn Isaacs
# This file is part of Sketch Grammar Explorer, licensed under BSD-3
# See the LICENSE file at https://github.com/engisalor/sketch-grammar-explorer/
"""Main module for executing API jobs."""
import argparse
import asyncio
import logging
import os
import shutil
import sys
from collections import Counter
from copy import deepcopy
from math import ceil
from pathlib import Path
from time import perf_counter

import aiohttp
import pandas as pd

from sgex import call as _call
from sgex import util

log_format = "%(message)s"
logging.basicConfig(format=log_format, level=logging.WARNING)

wait_dict = {"0": 9, "0.5": 99, "4": 899, "45": None}
default_servers = {
    "local": "http://localhost:10070/bonito/run.cgi",
    "ske": "https://api.sketchengine.eu/bonito/run.cgi",
}


class Job:
    """Main class for controlling the Sketch Engine API.

    Args:
        api_key: Server API key.
        cache_dir: Where data is saved.
        clear_cache: Clear the cache before executing.
        data: See `data` attribute.
        default_servers: Default servers to choose from.
        dry_run: Print job settings without executing.
        infile: Input file with lists of calls (JSON, JSONL, YAML).
        params: Call parameters.
        server: Active server for job.
        thread: Asynchronous requests.
        username: Server username.
        verbose: Print more details.
        wait_dict: Call throttling rules.

    Methods:
        run: Executes an instantiated `Job`.
        summary: Returns a summary of an executed `Job`.

    Attributes:
        data: Where call data is stored. See `call.Data` and `call.CachedResponse`
            dataclasses for more info.
    """

    def parse_params(self):
        """Loads calls from `params` and `infile` args and adds to `self.data`."""
        if not self.params_parsed:
            calls = self.params
            if self.infile:
                for f in [Path(x) for x in self.infile if x]:
                    if f.suffix == ".json":
                        calls.extend(util.read_json(f))
                    elif f.suffix == ".yml":
                        calls.extend(util.read_yaml(f))
                    elif f.suffix == ".jsonl":
                        calls.extend(pd.read_json(f, lines=True).to_dict("records"))
            for c in [x for x in calls if x]:
                params = {k: v for k, v in c.items() if k != "call_type"}
                self.data.add(getattr(_call, c["call_type"])(params))
            self.params_parsed = True

    def clear_cache_func(self):
        """Deletes the cache dir and all its content."""
        if self.clear_cache:
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(exist_ok=True)

    def dry_run_func(self):
        """Prints all settings for a dry run."""
        if self.dry_run:
            print("\nDRY RUN")
            print(self.__repr__())

    def set_wait(self):
        """Determines the wait period to use for a job's calls."""
        waits = []
        for k, v in self.wait_dict.items():
            if v:
                if self.data.len() <= v:
                    waits.append(float(k))
        if not waits:
            waits.append(max([float(k) for k in self.wait_dict.keys()]))
        self.wait = min(waits)

    async def send_call(
        self, call: _call.Call, session: aiohttp.ClientSession, **kwargs
    ) -> None:
        """Gets API data, whether it's cached locally or requires an API request."""
        file = Path(self.cache_dir) / Path(call.hash())
        _format = call.params.get("format", "json")
        call.response = _call.CachedResponse(
            file.with_suffix(".meta.json"), file.with_suffix(f".{_format}")
        )
        if call.response.file_meta.exists() and call.response.file_text.exists():
            call.response.get()
        else:
            if self.username and self.api_key:
                params = call.params | {
                    "username": self.username,
                    "api_key": self.api_key,
                }
            else:
                params = call.params
            if self.wait and not self.thread:
                self.wait_current += self.wait
                await asyncio.sleep(self.wait_current)
            async with session.get(
                url=self.server.rstrip("/") + "/" + call.type,
                params=params,
                **kwargs,
            ) as response:
                await call.response.set(response)

        return (call.response.ske_error, str(call))

    async def send_calls(self, get_kwargs: dict = {}, **kwargs):
        """Executes a list of calls."""
        if not self.dry_run:
            self.wait_current = 0 - self.wait
            if (
                not kwargs.get("timeout", None)
                and not get_kwargs.get("timeout", None)
                and self.server.startswith("http://localhost")
            ):
                logging.info("timeout disabled on localhost")
                kwargs["timeout"] = aiohttp.ClientTimeout(
                    total=None, connect=None, sock_connect=None, sock_read=None
                )
            if not self.thread:
                logging.info(f"sequential - wait {self.wait}")
                connector = aiohttp.TCPConnector(limit_per_host=1)
            else:
                connector = aiohttp.TCPConnector(limit_per_host=20)
                logging.info("concurrent")

            kwargs = dict(connector=connector, raise_for_status=True) | kwargs
            async with aiohttp.ClientSession(**kwargs) as session:
                res = await asyncio.gather(
                    *(
                        self.send_call(c, session, **get_kwargs)
                        for c in self.data.list()
                    ),
                    return_exceptions=True,
                )
                self.errors = []
                for x in range(len(res)):
                    if not isinstance(res[x], tuple):
                        self.errors.append((res[x], self.data.list()[x], x))
                    elif res[x][0] not in ["", "unimplemented"]:
                        self.errors.append(res[x] + (x,))

    def run(self, **kwargs):
        """Main function to execute a job.

        Args:
            kwargs: Arguments passed to the `aiohttp` session.
            get_kwargs: Can also be used to pass args to the `aiohttp` `get()` method.
        """
        t0 = perf_counter()
        self.cache_dir.mkdir(exist_ok=True)
        self.parse_params()
        self.set_wait()
        self.clear_cache_func()
        asyncio.run(self.send_calls(**kwargs))
        self.time = perf_counter() - t0
        if self.verbose:
            self.summary(True)
        self.dry_run_func()

    def run_repeat(self, max_pages=0, **kwargs):
        """Executes one View call repeatedly, incrementing `fromp` to more results.

        Args:
            max_pages: Limit the number of pages to retrieve (`0` is no limit).
            kwargs: Arguments passed to the `aiohttp` session.
            get_kwargs: Can also be used to pass args to the `aiohttp` `get()` method.

        Notes:
            - Only applies to call types with a `fromp` parameter (`View`).
            - Only accepts params dicts with a single call.
            - Use `Job.params["pagesize"]` to set the maximum hits per page
                (default = `100`).

        Examples:
            - Get all pages with `fromp=1` and `max_pages=0`.
            - Skip first two pages with `fromp=3` and `max_pages=0`.
            - Get pages 2-3 with `fromp=2` and `max_pages=2`.

        Warnings:
            - Keeping `thread=False` is recommended, especially for sizeable requests.
            - `pagesize` may exceed `100,000` to get many MB of data in one call, but
               large values or using `max_pages=0` to retrieve many concordances can
               cause server and memory issues.
        """
        if self.params[0]["call_type"] not in ["View"] or not len(self.params) == 1:
            raise ValueError("Only accepts one View call: `len(Job.params) == 1`")
        if self.dry_run:
            logging.warning("`dry_run` is not available for `run_repeat()`")
        if not self.params[0].get("fromp"):
            self.params[0]["fromp"] = 1
        logging.info("INITIAL CALL")
        self.run(**kwargs)
        _json = self.data.view[0].response.json()
        if _json["concsize"]:
            concsize = _json["concsize"]
        n_pages = ceil(concsize / self.params[0]["pagesize"])
        if n_pages == 1:
            logging.info(f"{concsize} hits retrieved - no additional calls needed")
        else:
            logging.info("SECONDARY CALLS")
            self.data = _call.Data()
            self.params_parsed = False
            self.clear_cache = False
            if not self.params[0].get("pagesize"):
                self.params[0]["pagesize"] = 100
            n_pages = n_pages - self.params[0]["fromp"] + 1
            if max_pages > 0 and max_pages < n_pages:
                n_pages = max_pages
            self.params = [deepcopy(self.params[0]) for x in range(n_pages)]
            for x in range(len(self.params)):
                self.params[x]["fromp"] = x + self.params[0]["fromp"]
            self.run(**kwargs)

    def summary(self, print_summary: bool = False) -> dict:
        "Returns a dict with a job execution summary, or prints if `summary(True)`."
        if not getattr(self, "time", None):
            if not print_summary:
                return {}
        else:
            dt = {"seconds": round(self.time, 4), "calls": self.data.len()}
            if not self.dry_run:
                dt |= {"errors": Counter([str(x[0]) for x in self.errors])}
        if not print_summary:
            return dt
        else:
            print(f'seconds  {dt["seconds"]}')
            print(f'calls    {dt["calls"]}')
            if not self.dry_run:
                print(f"errors   {len(self.errors)}")
                print("\n".join([f"- {v}    {k}" for k, v in dt["errors"].items()]))

    def __repr__(self) -> str:
        dt = {
            k: v for k, v in self.__dict__.items() if k not in ["data", "original_args"]
        }
        calls = "<class 'sgex.call.Data'>\n"
        calls += "\n".join(
            [
                f"{k} ({len(v)})    {v[:min(len(v), 3)]}"
                for k, v in self.data.__dict__.items()
                if v
            ]
        )
        attrs = "<class 'sgex.job.Job'>\n"
        for k, v in dt.items():
            if k not in ["username", "api_key"]:
                attrs += f"{(k)}    {str(v)[:min(len(str(v)), 80)]}\n"
            else:
                if v:
                    attrs += f"{(k)}    *\n"
                else:
                    attrs += f"{(k)}    None\n"
        return "\n".join([calls, attrs])

    def __init__(
        self,
        api_key: str | None = None,
        cache_dir: str = "data",
        clear_cache: bool = False,
        data: _call.Data = None,
        default_servers: dict = default_servers,
        dry_run: bool = False,
        infile: str | list | None = None,
        params: str | dict | list | None = None,
        server: str = "local",
        thread: bool = False,
        username: str | None = None,
        verbose: bool = False,
        wait_dict: dict = wait_dict,
    ) -> None:
        # original arguments
        self.api_key = api_key
        self.cache_dir = cache_dir
        self.clear_cache = clear_cache
        self.data = data
        self.default_servers = default_servers
        self.dry_run = dry_run
        self.infile = infile
        self.params = params
        self.server = server
        self.thread = thread
        self.username = username
        self.verbose = verbose
        self.wait_dict = wait_dict
        # additional args
        self.original_args = self.__dict__.copy()
        if self.verbose:
            logging.getLogger().setLevel(logging.INFO)
        else:
            logging.getLogger().setLevel(logging.WARNING)
        self.data = _call.Data()
        self.params_parsed = False
        self.server = self.default_servers.get(self.server, self.server)
        if self.server == "https://api.sketchengine.eu/bonito/run.cgi" and self.thread:
            logging.info("`thread` is disabled for the `ske` server")
            self.thread = False
        if not self.cache_dir:
            self.cache_dir = "data"
        self.cache_dir = Path(self.cache_dir)
        # enforce typing
        # parse objects
        for x in ["default_servers", "wait_dict", "params"]:
            val = getattr(self, x)
            val_parsed = util.parse_json_or_yaml(val)
            val = setattr(self, x, val_parsed)
        # str
        for x in ["api_key"]:
            val = getattr(self, x)
            if isinstance(val, int):
                setattr(self, x, str(val))
        # list
        for x in ["infile", "params"]:
            val = getattr(self, x)
            if not isinstance(val, list):
                setattr(self, x, [val])
        self.params = [util.parse_json_or_yaml(x) for x in self.params]
        # boolean
        for x in ["thread", "dry_run", "clear_cache", "verbose"]:
            val = getattr(self, x)
            if isinstance(val, str):
                if val.lower() == "true":
                    setattr(self, x, True)
                else:
                    setattr(self, x, False)
            if not isinstance(getattr(self, x), bool):
                raise TypeError(f"{x} must be type bool, not {type(val)}")


def parse_args(args):
    desc = "A controller for the Sketch Engine API"
    parser = argparse.ArgumentParser(prog="SGEX", description=desc)
    parser.add_argument(
        "-k",
        "--api-key",
        type=str,
        default=os.environ.get("SGEX_API_KEY"),
        help="API key, if required by server",
    )
    parser.add_argument(
        "--cache-dir",
        type=str,
        default=os.environ.get("SGEX_CACHE_DIR", "data"),
        help="cache directory",
    )
    parser.add_argument(
        "--clear-cache",
        action="store_true",
        default=os.environ.get("SGEX_CLEAR_CACHE", False),
        help="clear cache directory (no arguments; ignored if `--dry-run`)",
    )
    parser.add_argument(
        "--data",
        default=None,
        help="placeholder for API call data: not for CLI usage",
    )
    parser.add_argument(
        "--default-servers",
        default=os.environ.get("SGEX_DEFAULT_SERVERS", default_servers),
        help="settings for default servers",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=os.environ.get("SGEX_DRY_RUN", False),
        help="return assembled calls without sending (no arguments)",
    )
    parser.add_argument(
        "-i",
        "--infile",
        nargs="*",
        type=str,
        default=os.environ.get("SGEX_INFILE"),
        help="file to read call(s) from (accepts multiple args)",
    )
    parser.add_argument(
        "-p",
        "--params",
        nargs="*",
        default=os.environ.get("SGEX_PARAMS"),
        help="JSON/YAML string with a dict of params (accepts multiple args)",
    )
    parser.add_argument(
        "-s",
        "--server",
        default=os.environ.get("SGEX_SERVER", "local"),
        help="`local`, `ske` or a URL to another server",
    )
    parser.add_argument(
        "-x",
        "--thread",
        action="store_true",
        default=os.environ.get("SGEX_THREAD", False),
        help="run asynchronously, if allowed by server (no arguments)",
    )
    parser.add_argument(
        "-u",
        "--username",
        type=str,
        default=os.environ.get("SGEX_USERNAME"),
        help="API username, if required by server",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        default=os.environ.get("SGEX_VERBOSE", False),
        help="print details while running",
    )
    parser.add_argument(
        "-w",
        "--wait-dict",
        default=os.environ.get("SGEX_WAIT_DICT", wait_dict),
        help="wait period between calls",
    )
    return parser.parse_args(args)


if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    j = Job(**vars(args))
    j.run()
