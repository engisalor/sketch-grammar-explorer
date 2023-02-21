import logging
import os

from concurrent.futures import ThreadPoolExecutor, as_completed
from requests import Request, Response
from requests_cache import cache_keys, CachedSession
from time import perf_counter
from urllib.parse import parse_qs, urlparse

from sgex import config, wait


logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(module)s.%(funcName)s - %(message)s", level=logging.DEBUG
)

formats = ["json", "xml", "xls", "csv", "tsv", "txt"]
ignored_parameters = ['api_key', "username"]
types = [
    "attr_vals",
    "collx",
    "corp_info", 
    "extract_keywords",
    "freqml",
    "freqs", 
    "freqtt",
    "subcorp",
    "thes", 
    "view", 
    "wordlist",
    "wsdiff",
    "wsketch", 
    ]


class Call:
    def validate(self):
        if self.params.get("format"):
            if self.params["format"] not in formats:
                raise ValueError(f"format must be one of {formats}: {self.dt}")
        for p in self.required:
            if not self.params.get(p):
                raise ValueError(f"{p} missing: {self.dt}")

    def __repr__(self) -> str:
        return f"{self.type.upper()}: {self.params}"

    def __init__(self, type, params, required=["corpname"]):
        self.type = type
        self.params = params
        self.required = set(required)
        self.dt = {"type": self.type, **self.params}
        if self.type not in types:
            raise ValueError(f"type must be one of {types}")
        if not isinstance(self.params, dict):
            raise TypeError("params must be a dict")


class Attr_vals(Call):
    def __init__(self, params):
        super().__init__("attr_vals", params, ["corpname", "avattr"])

class Collx(Call):
    def __init__(self, params):
        super().__init__("collx", params, ["corpname", "q"])

class Corp_info(Call):
    def __init__(self, params):
        super().__init__("corp_info", params, ["corpname"])

class extract_keywords(Call):
    def __init__(self, params):
        super().__init__("extract_keywords", params, ["corpname"])

class Freqs(Call):
    def __init__(self, params):
        super().__init__("freqs", params, ["corpname", "q", "fcrit"])

class Freqml(Call):
    def __init__(self, params):
        super().__init__("freqml", params, ["corpname", "q", "fcrit"])

class Freqtt(Call):
    def __init__(self, params):
        super().__init__("freqtt", params, ["corpname", "q", "fcrit"])

class Subcorp(Call):
    def __init__(self, params):
        super().__init__("subcorp", params, ["corpname"])

class Thes(Call):
    def __init__(self, params):
        super().__init__("thes", params, ["corpname", "lemma"])

class Wordlist(Call):
    def __init__(self, params):
        super().__init__("wordlist", params, ["corpname", "wltype", "wlattr"])

class Wsdiff(Call):
    def __init__(self, params):
        super().__init__("wsdiff", params, ["corpname", "lemma", "lemma2"])

class Wsketch(Call):
    def __init__(self, params):
        super().__init__("wsketch", params, ["corpname", "lemma"])

class View(Call):
    def __init__(self, params):
        if not params.get("asyn"):
            params["asyn"] = 0
        super().__init__("view", params, ["corpname", "q"])


class Package:
    def send_requests(self) -> None:
        timeout = wait.timeout(len(self.calls), self.conf[self.server])
        # NOTE response hook fires twice per request, thus 'timeout / 2'
        self.session.hooks['response'].append(wait.make_hook(timeout / 2)) 
        t0 = perf_counter()
        for x in range(len((self.calls))):
            response = self.session.get(
                self.calls[x].request.url, 
                params = self.calls[x].request.params)
            self._manage_response(response, t0)
        logging.debug(f'{len(self.calls)} - {perf_counter() - t0:.3f}s - {len(self.errors)} errors')


    def send_async_requests(self, **kwargs) -> None:
        if not self.conf[self.server].get("asynchronous"):
            raise ValueError(f"async calling not enabled for {self.server} server")
        t0 = perf_counter()
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_url = {executor.submit(self.session.get, c.request.url, params = c.request.params): c for c in self.calls}
            for future in as_completed(future_to_url):
                response = future.result()
                self._manage_response(response, t0)
        logging.debug(f'{len(self.calls)} - {perf_counter() - t0:.3f}s - {len(self.errors)} errors')

    def _manage_response(self, response: Response, t0: float) -> None:
        self._add_response_to_instance(response)
        self._handle_errors(response)


    def _add_response_to_instance(self, response: Response) -> None:
        if self.max_responses >= len(self.responses):
            self.responses.append(response)


    def _handle_errors(self, response: Response) -> None:
        response.raise_for_status()
        if response.status_code >= 400:
            error = ": ".join([str(response.status_code), response.reason])
        elif "application/json" in response.headers.get('content-type'):
            error = response.json().get("error", None)
        if error:
            query = parse_qs(urlparse(response.url).query)
            dt = {k:v for k,v in query.items() if k not in ignored_parameters}
            host = response.url.split("?")[0]
            self.errors.add((error, host, str(dt)))
            logging.warning(f'{error} - {host} - {dt}')
        if error and self.halt:
            raise Warning(f"requests halted with error: {error}")


    def __init__(self, calls: list[Call], server: str, **kwargs):
        self.calls = calls
        self.server= server
        self.halt = True
        self.errors = set()
        self.max_workers = min(32, os.cpu_count() + 4)
        self.responses = []
        self.max_responses = 100
        self.session_params = dict(
            cache_name='data/file_cache',
            serializer= "json",
            backend='filesystem',
            ignored_parameters=ignored_parameters,
            allowable_codes=[200, 400, 500],
        )
        self.conf_params = dict(source=".config.yml")
        # use kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)
        # run
        self.conf = config.load(**self.conf_params)
        self.session = CachedSession(**self.session_params)
        prepare(self.calls,self.server, self.conf)


def prepare(calls: list[Call], server: str, conf: dict, **kwargs) -> None:
    creds = {k:v for k,v in conf[server].items() if k in ignored_parameters}
    propagate(calls)
    for call in calls:
        call.validate()
    add_creds(calls, creds)
    add_request(calls, server, conf, **kwargs)
    add_key(calls)


def propagate_key(calls: list[Call], key: str) -> None:
    for x in range(1, len(calls)):
        # ignore if type changes
        if calls[x].type != calls[x-1].type:
            pass
        # merge if value is a dict
        elif isinstance(calls[x-1].params.get(key), dict) and isinstance(
            calls[x].params.get(key), dict
        ):
            calls[x].params[key] = {
                **calls[x-1].params.get(key),
                **calls[x].params.get(key),
            }
        # ignore existing non-dict values
        elif calls[x].params.get(key):
            pass
        # reuse missing non-dict values
        elif calls[x-1].params.get(key):
            calls[x].params[key] = calls[x-1].params.get(key)
        else:
            pass

def propagate(calls: list[Call]) -> None:
    keys = set([k for call in calls for k in call.params.keys()])
    for k in keys:
        propagate_key(calls, k) 
    return calls


def add_creds(calls: list[Call], creds:dict) -> None:
    for x in range(len(calls)):
        calls[x].params = {**creds, **calls[x].params}


def add_request(calls: list[Call], server: str, conf, **kwargs) -> None:
    for x in range(len(calls)):
        calls[x].request = Request(
            "GET", 
            url= "/".join([conf[server]["host"], calls[x].type]),
            params=calls[x].params,
            **kwargs,
        )


def add_key(calls: list[Call], **kwargs) -> None:
    for x in range(len(calls)):
        calls[x].key = cache_keys.create_key(
        calls[x].request,
        ignored_parameters=ignored_parameters,
        **kwargs,
        )

