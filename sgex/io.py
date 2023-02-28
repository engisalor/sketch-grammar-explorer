"""Read/write functions."""
import json
import pathlib
from urllib.parse import parse_qs, urlparse

import pandas as pd
import yaml
from requests import Response


def read_yaml(file: str) -> dict:
    with open(file) as stream:
        dt = yaml.safe_load(stream)
    return dt


def read_json(file: str) -> dict:
    with open(file) as f:
        dt = json.load(f)
    return dt


def overwrite(file: str, replace: bool = True, prompt: bool = False) -> bool:
    """Manages overwriting of preexisting files with replace/prompt args."""
    if pathlib.Path(file).exists() and prompt:
        m = f"Overwrite {file}? (y/N): "
        if input(m).lower() != "y":
            replace = False
        else:
            replace = True
    elif not pathlib.Path(file).exists():
        replace = True
    return replace


def write_yaml(file: str, dt: dict, replace=True, prompt: bool = True) -> None:
    replace = overwrite(file, replace=replace, prompt=prompt)
    if replace:
        with open(file, "w", encoding="utf-8") as f:
            yaml.dump(
                dt,
                f,
                allow_unicode=True,
                indent=2,
            )


def write_json(file: str, dt: dict, prompt: bool = True) -> None:
    replace = overwrite(file, replace=overwrite, prompt=prompt)
    if replace:
        with open(file, "w", encoding="utf-8") as f:
            json.dump(dt, f, indent=2, ensure_ascii=False)


def to_csv(response: Response, filename: str = "content"):
    filename = pathlib.Path(filename).with_suffix(".csv")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(response.text)


def to_json(response: Response, filename: str = "content"):
    filename = pathlib.Path(filename).with_suffix(".json")
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(response.json(), f, ensure_ascii=False, indent=1)


def to_txt(response: Response, filename: str = "content"):
    filename = pathlib.Path(filename).with_suffix(".txt")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(response.text)


def to_xlsx(response: Response, filename: str = "content"):
    filename = pathlib.Path(filename).with_suffix(".xlsx")
    xlsx = pd.read_excel(response.content, header=None)
    xlsx.to_excel(filename, header=False, index=False)


def to_xml(response: Response, filename: str = "content"):
    filename = pathlib.Path(filename).with_suffix(".xml")
    from defusedxml import ElementTree as etree

    xml = etree.fromstring(response.content)
    with open(filename, "wb") as f:
        f.write(
            etree.tostring(
                xml,
                encoding="UTF-8",
                xml_declaration=True,
            )
        )


def export_content(response: Response, filename: str = "content"):
    """Exports the content of a Response to its native format.

    Args:
        response: A ``Response`` object.
        filename: Name for the generated file (the extension is set automatically).

    Notes:
        Output formats: ``["json", "xml", "xls", "csv", "txt"]``.

        The availability of these formats depends on the API call (freqs, view, etc.)
        and the server being used. Only JSON is universally available.

    Raises:
        If an error is raised, check ``Response.content`` for any internal SkE errors.
        Try making the same API call with ``"format": "json"``.
    """
    query = parse_qs(urlparse(response.url).query)
    _format = query.get("format", ["json"])[0]
    if _format == "json":
        to_json(response, filename)
    elif _format == "xml":
        to_xml(response, filename)
    elif _format == "csv":
        to_csv(response, filename)
    elif _format == "txt":
        to_txt(response, filename)
    elif _format in ["xls", "xlsx"]:
        to_xlsx(response, filename)
    else:
        raise ValueError(f"unable to export to {_format}: {response.content}")
