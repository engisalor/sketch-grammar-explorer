import pathlib
import json
import yaml


def parse(input, dest=None):
    """Parses and returns/saves a JSON/YAML file or dict of API calls.

    `dest="<filepath.extension>"` saves object to file (.json, .yml, .yaml)
    - (can be used to convert between file formats)
    """

    # Load calls
    if isinstance(input, dict):
        calls = input
    elif isinstance(input, str):
        input = pathlib.Path(input)
        if not input.exists():
            raise FileNotFoundError
        else:
            if input.suffix in [".yml", ".yaml"]:
                with open(input, "r") as stream:
                    calls = yaml.safe_load(stream)
            elif input.suffix == ".json":
                with open(input, "r") as f:
                    calls = json.load(f)
            else:
                raise ValueError("Unknown format (use .json .yml .yaml)")
    else:
        raise ValueError("Unknown format (use dict or str w/ extension .json .yml .yaml)")

    # Save
    if dest:
        output_file = pathlib.Path(dest)
        if output_file.suffix == ".json":
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(calls, f, ensure_ascii=False, indent=2)
        elif output_file.suffix in [".yml", ".yaml"]:
            with open(output_file, "w", encoding="utf-8") as f:
                yaml.dump(
                    calls, f, allow_unicode=True, sort_keys=False, indent=2
                )
        else:
            raise ValueError("Unknown output format: use .json .yml .yaml")
    # Return
    else:
        return calls
