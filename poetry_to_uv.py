#!/usr/bin/env python
import argparse
import re
from pathlib import Path

import toml

gt_version = re.compile(r"\^(\d.*)")


def argparser() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="poetry_to_uv",
        description="Poetry to Uv pyproject conversion",
        epilog="It will move the original pyproject.toml to pyproject.toml.org",
    )
    parser.add_argument("filename")
    parser.add_argument(
        "-n", action="store_true", help="Do not backup and create pyproject.toml"
    )
    return parser.parse_args()


def version_conversion(version: str) -> str:
    if version == "*":
        return ""
    elif found := gt_version.match(version):
        return f">={found.group(1)}"
    else:
        print(f"Well, this is an unexpected version\nVersion = {version}\n")
        raise ValueError


def authors(uv_toml: dict):
    user_email = re.compile(r"^([\w ]+) <([\w@.]+)>$")

    if authors := uv_toml["project"].get("authors"):
        if isinstance(authors, list) and len(authors) == 1:
            user_email.match(authors[0])
            try:
                name, email = user_email.match(authors[0]).groups()
            except AttributeError:
                name, email = ("example", "example@gmail.com")
                uv_toml["project"]["authors_to_delete"] = authors
            uv_toml["project"]["authors"] = (
                f"[{{'name' = '{name}', 'email' = '{email}'}}]"
            )
    else:
        uv_toml["project"]["authors"] = (
            "[{{'name' = 'example', 'email' = 'example@email.com'}}]"
        )


def python_version(uv_toml: dict):
    # check specific python version
    if not uv_toml["project"]["dependencies"].get("python"):
        print("No python version found")
        return
    uv_toml["project"]["requires-python"] = version_conversion(
        uv_toml["project"]["dependencies"]["python"]
    )
    del uv_toml["project"]["dependencies"]["python"]


def dev_dependencies(uv_toml: dict) -> None:
    # dev dependencies
    if not (
        deps := uv_toml["project"]
        .get("group", {})
        .get("dev", {})
        .get("dependencies", {})
    ):
        return
    if uv_toml["project"].get("group", {}).get("dev", {}).get("optional", ""):
        print("The Dev optional flag is ignored. You'll have to take care of this!")

    uv_deps = []

    uv_deps = parse_packages(deps, uv_deps)
    uv_toml["dependency-groups"] = {"dev": uv_deps}
    del uv_toml["project"]["group"]["dev"]


def parse_packages(deps, uv_deps) -> list[str]:
    for name, version in deps.items():
        extra = ""

        if isinstance(version, dict):
            # deal with extras
            if e := version.get("extras"):
                v = version["version"]
                for i in e:
                    extra = f"[{i}]"
                    uv_deps.append(f"{name}{extra}{version_conversion(v)}")
                continue

        uv_deps.append(f"{name}{extra}{version_conversion(version)}")
    return uv_deps


def dependencies(uv_toml: dict) -> None:
    # dev dependencies
    if not (deps := uv_toml["project"].get("dependencies", {})):
        return
    uv_deps = []

    uv_deps = parse_packages(deps, uv_deps)
    uv_toml["project"]["dependencies"] = uv_deps


def tool(uv_toml: dict, pyproject_data: dict):
    # deal with other tools
    for tool, data in pyproject_data["tool"].items():
        if tool == "poetry":
            continue
        uv_toml["tool"][tool] = data


def main():
    args = argparser()
    project_file = Path(args.filename)
    dry_run = args.n
    project_dir = project_file.parent
    backup_file = project_dir / f"{project_file.name}.org"
    if dry_run:
        output_file = Path(project_dir / "pyproject_temp_uv.toml")
        print(f"Dry_run enabled. Output file: {output_file}")
    else:
        print(f"Replacing {project_file}.\nBackup file : {backup_file}")
        output_file = project_file
    print()

    with project_file.open("r") as f:
        pyproject_data = toml.load(f)

    uv_toml = {"tool": {}, "project": pyproject_data["tool"]["poetry"]}
    authors(uv_toml)
    python_version(uv_toml)
    dev_dependencies(uv_toml)
    dependencies(uv_toml)
    tool(uv_toml, pyproject_data)
    if "group" in uv_toml["project"]:
        del uv_toml["project"]["group"]

    if not dry_run:
        project_file.rename(backup_file)

    with output_file.open("w") as f:
        toml.dump(uv_toml, f)

    print("Actions required:")
    print("* Change the authors. Remove the double quotes on both sides")
    print("\t e.g. authors = [{ 'name' = 'First Last', 'email' = 'first@domain.nl' }]")
    print("\t* https://packaging.python.org/en/latest/guides/writing-pyproject-toml/")
    print("* if any '\\n' or '\\t' are found, make it pretty yourself.")


if __name__ == "__main__":
    main()
