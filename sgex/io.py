import yaml
import json
import pathlib
from requests import Response


def read_yaml(file: str) -> dict:
    with open(file) as stream:
        dt = yaml.safe_load(stream)
    return dt


def read_json(file:str) -> dict:
    with open(file) as f:
        dt = json.load(f)
    return dt


def overwrite(file:str, replace:bool=True, prompt:bool=False) -> bool:
    if pathlib.Path(file).exists() and prompt:
        m = f"Overwrite {file}? (y/N): "
        if input(m).lower() != "y":
            replace = False
        else:
            replace = True
    elif not pathlib.Path(file).exists():
        replace = True
    return replace


def write_yaml(file: str, dt:dict, replace=True, prompt:bool =True) -> None:
    replace = overwrite(file, replace=replace, prompt=prompt)
    if replace:
        with open(file, "w", encoding="utf-8") as f:
            yaml.dump(dt, f, allow_unicode=True, indent=2,)


def write_json(file: str, dt:dict, prompt:bool =True) -> None:
    replace = overwrite(file, replace=overwrite, prompt=prompt)
    if replace:
        with open(file, "w", encoding="utf-8") as f:
            json.dump(dt, f, indent=2, ensure_ascii=False)


def data_to_csv(file: str, response: Response):
    with open(file, "w", encoding="utf-8") as f:
        f.write(response.text)


def data_to_json(file: str, response: Response):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(response.json(), f, ensure_ascii=False, indent=1)


def data_to_txt(file: str, response: Response):
    with open(file, "w", encoding="utf-8") as f:
        f.write(response.text)


def data_to_xlsx(file: str, response: Response):
    import pandas as pd

    xlsx = pd.read_excel(response.content, header=None)
    xlsx.to_excel(file, header=False, index=False)


def data_to_xml(file: str, response: Response):
    from lxml import etree

    xml = etree.fromstring(response.content)
    with open(file, "wb") as f:
        f.write(
            etree.tostring(
                xml,
                encoding="UTF-8",
                xml_declaration=True,
                pretty_print=True,
            )
        )
