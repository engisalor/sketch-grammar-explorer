"""For organizing and executing API calls."""
import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from time import perf_counter
from urllib.parse import parse_qs, urlparse

from requests import Response
from requests_cache import CachedSession

from sgex import config
from sgex.call import call, hook
from sgex.call.type import Call
from sgex.config import ignored_parameters

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(module)s.%(funcName)s - %(message)s",
    level=logging.DEBUG,
)


class Package:
    """Class for organizing and executing API calls."""

    def send_requests(self) -> None:
        """Executes Calls sequentially with a wait period if uncached & required."""
        wait = hook.wait(len(self.calls), self.conf[self.server])
        # NOTE response hook fires twice per request, thus 'wait / 2'
        self.session.hooks["response"].append(hook.wait_hook(wait / 2))
        t0 = perf_counter()
        for x in range(len((self.calls))):
            response = self.session.get(
                self.calls[x].request.url, params=self.calls[x].request.params
            )
            self._manage_response(response, t0)
        t1 = perf_counter()
        logging.debug(f"{len(self.calls)} - {t1-t0:.3f}s - {len(self.errors)} errors")

    def send_async_requests(self, **kwargs) -> None:
        """Executes Calls asynchronously (if allowed for a server)."""
        if not self.conf[self.server].get("asynchronous"):
            raise ValueError(f"async calling not enabled for {self.server} server")
        t0 = perf_counter()
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
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
        logging.debug(f"{len(self.calls)} - {t1-t0:.3f}s - {len(self.errors)} errors")

    def _manage_response(self, response: Response, t0: float) -> None:
        self._add_response_to_instance(response)
        self._handle_errors(response)

    def _add_response_to_instance(self, response: Response) -> None:
        if self.max_responses >= len(self.responses):
            self.responses.append(response)

    def _handle_errors(self, response: Response) -> None:
        error = None
        response.raise_for_status()
        if response.status_code >= 400:
            error = ": ".join([str(response.status_code), response.reason])
        elif "application/json" in response.headers.get("content-type"):
            error = response.json().get("error", None)
        if error:
            query = parse_qs(urlparse(response.url).query)
            dt = {k: v for k, v in query.items() if k not in ignored_parameters}
            host = response.url.split("?")[0]
            self.errors.add((error, host, str(dt)))
            logging.warning(f"{error} - {host} - {dt}")
        if error and self.halt:
            raise Warning(f"requests halted with error: {error}")

    def __init__(self, calls: list[Call], server: str, **kwargs):
        if isinstance(calls, Call):
            calls = [calls]
        self.calls = calls
        self.server = server
        self.halt = True
        self.errors = set()
        self.max_workers = min(32, os.cpu_count() + 4)
        self.responses = []
        self.max_responses = 100
        self.session_params = dict(
            cache_name="data/file_cache",
            serializer="json",
            backend="filesystem",
            ignored_parameters=ignored_parameters,
            allowable_codes=[200, 400, 500],
            key_fn=call.create_key_from_params,
        )
        self.conf_params = dict(source=".config.yml")
        # use kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)
        # run
        self.conf = config.load(**self.conf_params)
        self.session = CachedSession(**self.session_params)
        self.session.hooks["response"].append(hook.redact_hook())
        call.prepare(self.calls, self.server, self.conf)
