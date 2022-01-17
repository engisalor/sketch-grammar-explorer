import pathlib

import sge


def examples(dir="calls", format=".yml", overwrite=False):
    """Generate example input files to `dir` with format `.yml` or `.json`).

    `overwrite=True` skips warning for existing files
    """

    path = pathlib.Path(dir)
    print(f'Saving example calls to "{dir}/"')

    for k, v in sge.data.json_tests.items():
        file = path / pathlib.Path(k).with_suffix(format)

        yn = "y"

        if file.exists() and not overwrite:
            yn = input(f'Overwrite "{file}"? (y/N) ')

        if yn == "y":
            path.mkdir(parents=True, exist_ok=True)
            sge.Parse(v, dest=file)
        else:
            pass

    print("Done")
