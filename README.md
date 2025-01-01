# poetry_to_uv

The poetry_to_uv.py script is meant to easily set the base for the pyproject.toml to be consumed by `uv` instead of `poetry`.

**It is not foolproof!**

It has a dry-run flag, to have a temporary file to validate the output. When not running the dry-run the original file is saved with a .org extension.

    uv run poetry_to_uv.py <path to file> [-n]

You may need to make some manual changes. Certain layout things are best done with [Even better toml](https://marketplace.visualstudio.com/items?itemName=tamasfe.even-better-toml) in VSCode. Just open the newly generated toml file and save. It will format the file according to the toml specification.

## Notes
* If you were using the poetry build-system, it will be replaced by hatchling.
* if you had optional dev groups, the dev group libraries will be used, the optional flag is removed

# Using as a tool
The script can be run as a tool using [`uvx`](https://docs.astral.sh/uv/guides/tools/)

    uvx --from git+https://github.com/bartdorlandt/poetry_to_uv poetry-to-uv --help

# Contribute
Feel free to contribute to the code.

Cheers, Bart Dorlandt