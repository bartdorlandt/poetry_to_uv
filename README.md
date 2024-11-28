# poetry_to_uv

The script in this repo is meant to easily set the base for the pyproject.toml to be consumed by `uv` instead of `poetry`.

It is not foolproof!

It has a dry-run flag, to have a temporary file to validate the output. When not running the dry-run the original file is saved with a .org extension.

    poetry_to_uv.py <path to file> [-n]

You'll need to make some manual changes, probably around the following:

* authors or other parts, that have lists in them. They might be seen as chapters in the toml, instead of the literal array syntax.
* tool sections that use the multiline syntax in the exclude commands (ruff, mypy, black, ...)
* Other multiline parts
* if you had optional dev groups, the dev group libraries will be used, the optional flag is removed
* Comments are lost

# Contribute
Feel free to contribute to the code.

Cheers, Bart Dorlandt