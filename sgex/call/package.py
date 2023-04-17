"""For organizing and executing API calls."""
import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from time import perf_counter
from urllib.parse import parse_qs, urlparse

from requests import Response
from requests_cache import CachedSession

from sgex.call import call, hook
from sgex.call.type import Call
from sgex.config import credential_parameters, default
from sgex.config import load as load_config


class Package:
    """Class for organizing and executing API calls."""

    def send_requests(self) -> None:
        """Executes Calls sequentially with a wait period if uncached & required."""
        wait = hook.wait(len(self.calls), self.config[self.server])
        # NOTE response hook fires twice per request, thus 'wait / 2'
        self.session.hooks["response"].append(hook.wait_hook(wait / 2))
        t0 = perf_counter()
        for x in range(len((self.calls))):
            response = self.session.get(
                self.calls[x].request.url, params=self.calls[x].request.params
            )
            self._manage_response(response, t0)
        t1 = perf_counter()
        logging.info(f"{len(self.calls)} - {t1-t0:.3f}s - {len(self.errors)} errors")

    def send_async_requests(self, **kwargs) -> None:
        """Executes Calls asynchronously (if allowed for a server)."""
        if not self.config[self.server].get("asynchronous"):
            raise ValueError(f"async calling not enabled for {self.server} server")
        t0 = perf_counter()
        with ThreadPoolExecutor(max_workers=self.max_workers, **kwargs) as executor:
            future_to_url = {
                executor.submit(
                    self.session.get, c.request.url, params=c.request.params
                ): c
                for c in self.calls
            }
            for future in as_completed(future_to_url):
                response = future.result()
                self._manage_response(response, t0)
        t1 = perf_counter()
        logging.info(f"{len(self.calls)} - {t1-t0:.3f}s - {len(self.errors)} errors")

    def _manage_response(self, response: Response, t0: float) -> None:
        self._add_response_to_instance(response)
        self._handle_errors(response)

    def _add_response_to_instance(self, response: Response) -> None:
        if self.max_responses >= len(self.responses):
            self.responses.append(response)
            if self.max_responses == len(self.responses):
                m = f"reached max_responses ({self.max_responses})"
                logging.warning(m)

    def _handle_errors(self, response: Response) -> None:
        error = None
        # HTTP errors
        response.raise_for_status()
        # Sketch Engine errors
        # TODO include other formats (CSV, etc.)
        if "application/json" in response.headers.get("content-type"):
            error = response.json().get("error", None)
        if error:
            query = parse_qs(urlparse(response.url).query)
            dt = {k: v for k, v in query.items() if k not in credential_parameters}
            host = response.url.split("?")[0]
            self.errors.add((error, host, str(dt)))
            logging.warning(f"{error} - {host} - {dt}")
        if error and self.halt:
            raise Warning(f"requests halted with error: {error}")

    def __init__(self, calls: list, server: str, config: dict = default, **kwargs):
        if isinstance(calls, Call):
            calls = [calls]
        self.calls = calls
        self.server = server
        self.halt = True
        self.errors = set()
        self.loglevel = "warning"
        self.max_workers = min(32, os.cpu_count() + 4)
        self.responses = []
        self.max_responses = 100
        self.session_params = dict(
            cache_name="data/file_cache",
            serializer="json",
            backend="filesystem",
            ignored_parameters=credential_parameters,
            key_fn=call.create_custom_key,
        )
        self.config = load_config(config)
        # use kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)

        # logging
        numeric_level = getattr(logging, self.loglevel.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError(f"Invalid log level: {self.loglevel}")
        m = "%(asctime)s - %(levelname)s - %(module)s.%(funcName)s - %(message)s"
        logging.basicConfig(
            format=m,
            level=numeric_level,
        )

        # run
        self.session = CachedSession(**self.session_params)
        self.session.hooks["response"].append(hook.redact_hook())
        call.prepare(self.calls, self.server, self.config)
