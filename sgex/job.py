#!/usr/bin/python3
"""Main module for executing API jobs."""
import argparse
import asyncio
import json
import os
import shutil
import sys
from pathlib import Path
from time import perf_counter, sleep

import aiofiles
import aiohttp
import pandas as pd
from yarl import URL

from sgex import call as call
from sgex import util

wait_dict = {"0": 9, "0.5": 99, "4": 899, "45": None}
default_servers = {
    "local": "http://localhost:10070/bonito/run.cgi",
    "ske": "https://api.sketchengine.eu/bonito/run.cgi",
}


class CachedResponse:
    """A mock Response class for managing caching."""

    @staticmethod
    def redact_json(dt: dict) -> str:
        """Removes API credentials from a dict."""
        if dt.get("request"):
            dt["request"].pop("username", None)
            dt["request"].pop("api_key", None)
        return dt

    @staticmethod
    def redact_url(url: URL) -> URL:
        """Removes API credentials from a yarl url."""
        dt = {k: v for k, v in url.query.items() if k not in ["username", "api_key"]}
        return url.with_query(dt)

    async def set(self, response: aiohttp.ClientResponse):
        """Parses a Response and saves to cache."""
        meta = {
            "url": str(self.redact_url(response.url)),
            "status": response.status,
            "reason": response.reason,
            "headers": dict(response.headers),
        }
        if "application/json" in response.headers.get("Content-Type"):
            j = await response.json()
            meta["ske_error"] = j.get("error", None)
            self.text = json.dumps(self.redact_json(j), indent=2)
        else:
            meta["ske_error"] = "not implemented"
            self.text = await response.text()
            self.text = self.text.lstrip("\ufeff")
        for k, v in meta.items():
            setattr(self, k, v)
        async with aiofiles.open(self.file_meta, "w") as f:
            await f.write(json.dumps(meta, indent=2))
        async with aiofiles.open(self.file_text, "w") as f:
            await f.write(self.text)

    def get(self):
        """Retrieves a cached response."""
        dt = util.read_json(self.file_meta)
        with open(self.file_text) as f:
            dt |= {"text": f.read()}
        for k, v in dt.items():
            setattr(self, k, v)

    def __init__(self, file_meta: Path, file_text: Path) -> None:
        self.file_meta = file_meta
        self.file_text = file_text
        self.is_cached = False
        if self.file_meta.exists() and self.file_text.exists():
            self.is_cached = True


class Job:
    """Main class for controlling the Sketch Engine API."""

    def parse_file(self):
        """Loads calls from a json/jsonl/yaml file."""
        if self.infile:
            for f in [Path(x) for x in self.infile if x]:
                if f.suffix == ".json":
                    self.calls.extend(util.read_json(f))
                elif f.suffix == ".yml":
                    self.calls.extend(util.read_yaml(f))
                elif f.suffix == ".jsonl":
                    self.calls.extend(pd.read_json(f, lines=True).to_dict("records"))

    def clear_cache_func(self):
        """Deletes the cache dir and all its content."""
        if self.clear_cache:
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(exist_ok=True)

    def assemble_calls(self):
        """Converts parameters from input sources to `call.Call` objects."""
        self.calls = [
            getattr(call, self.call_type)(
                {"corpname": self.corpus, "format": self.format} | p
            )
            for p in self.calls
            if p
        ]
        self.calls_len = len(self.calls)

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
                if len(self.calls) <= v:
                    waits.append(float(k))
        if not waits:
            waits.append(max([float(k) for k in self.wait_dict.keys()]))
        self.wait = min(waits)

    async def send_call(self, call, session, **kwargs) -> None:
        """Gets API data, whether it's cached locally or requires an API request."""
        file = Path(self.cache_dir) / Path(call.to_hash())
        call.response = CachedResponse(
            file.with_suffix(".meta.json"), file.with_suffix(f".{self.format}")
        )
        if call.response.is_cached:
            call.response.get()
        else:
            async with session.get(
                url=self.server.rstrip("/") + "/" + call.type,
                params=call.params
                | {"username": self.username, "api_key": self.api_key},
                **kwargs,
            ) as response:
                print(str(call))
                response.raise_for_status()
                await call.response.set(response)

    async def send_sequential_calls(self):
        """Executes job calls sequentially."""
        if not self.dry_run and not self.thread:
            print(f"... sequential - {self.wait}s wait")
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                for x in range(len(self.calls)):
                    await self.send_call(self.calls[x], session, timeout=self.timeout)
                    if x < len(self.calls) - 1:
                        sleep(self.wait)

    async def send_async_calls(self):
        """Executes job calls asychronously."""
        if not self.dry_run and self.thread:
            print("... concurrent")
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                await asyncio.gather(
                    *(
                        self.send_call(call, session, timeout=self.timeout)
                        for call in self.calls
                    )
                )

    def run(self):
        """Main function to execute a job."""
        t0 = perf_counter()
        self.cache_dir.mkdir(exist_ok=True)
        self.calls += self.params
        self.parse_file()
        self.assemble_calls()
        self.set_wait()
        self.clear_cache_func()
        self.timeout = aiohttp.ClientTimeout(total=self.timeout)
        asyncio.run(self.send_sequential_calls())
        asyncio.run(self.send_async_calls())
        self.dry_run_func()
        print(round(perf_counter() - t0, 4))

    def __repr__(self) -> str:
        dt = {
            k: v
            for k, v in self.__dict__.items()
            if k not in ["calls", "original_args"]
        }
        calls = "____Calls____\n"
        calls += "\n".join(
            [str(self.calls[x]) for x in range(len(self.calls)) if x < 10]
        )
        attrs = "____Attributes____\n"
        attrs += "\n".join(
            sorted(
                [
                    f'{(k)}    {(v if not k in ["username", "api_key"] else "*")}'
                    for k, v in dt.items()
                ]
            )
        )
        return "\n".join([calls, attrs])

    def __init__(
        self,
        api_key: str | None = None,
        cache_dir: str = "data",
        call_type: str | None = None,
        clear_cache: bool = False,
        corpus: str | None = None,
        default_servers: dict = default_servers,
        dry_run: bool = False,
        format: str = "json",
        infile: str | list | None = None,
        params: str | list | None = None,
        server: str = "local",
        thread: bool = False,
        timeout: int = 30,
        username: str | None = None,
        wait_dict: dict = wait_dict,
    ) -> None:
        # original arguments
        self.api_key = api_key
        self.cache_dir = cache_dir
        self.call_type = call_type
        self.clear_cache = clear_cache
        self.corpus = corpus
        self.default_servers = default_servers
        self.dry_run = dry_run
        self.format = format
        self.infile = infile
        self.params = params
        self.server = server
        self.thread = thread
        self.timeout = timeout
        self.username = username
        self.wait_dict = wait_dict
        # additional args
        self.original_args = self.__dict__.copy()
        self.server = self.default_servers.get(self.server, self.server)
        self.calls = []
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
        # numeric
        for x in ["timeout"]:
            val = getattr(self, x)
            if isinstance(val, str) and "." in val:
                setattr(self, x, float(val))
            else:
                setattr(self, x, int(val))
        # boolean
        for x in ["thread", "dry_run", "clear_cache"]:
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
        "-t",
        "--call-type",
        choices=[x.__name__ for x in call.Call.__subclasses__()],
        default=os.environ.get("SGEX_CALL_TYPE"),
        help="API call type",
    ),
    parser.add_argument(
        "--clear-cache",
        action="store_true",
        default=os.environ.get("SGEX_CLEAR_CACHE", False),
        help="clear cache directory (no arguments; ignored if `--dry-run`)",
    )
    parser.add_argument(
        "-c",
        "--corpus",
        type=str,
        default=os.environ.get("SGEX_CORPUS"),
        help="corpus name (with path, if any: `preloaded/<corpus>`)",
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
        "-f",
        "--format",
        choices=["json", "xml", "xlsx", "csv", "txt"],
        default=os.environ.get("SGEX_FORMAT", "json"),
        help="API data output format",
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
        "-z",
        "--timeout",
        type=int,
        default=os.environ.get("SGEX_TIMEOUT", 30),
        help="request timeout",
    )
    parser.add_argument(
        "-u",
        "--username",
        type=str,
        default=os.environ.get("SGEX_USERNAME"),
        help="API username, if required by server",
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
