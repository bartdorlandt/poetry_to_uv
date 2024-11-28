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
    # deal with authors
    # May need to improve this part
    # if authors := uv_toml["project"].get("authors"):
    #     if isinstance(authors, list) and len(authors) == 1:
    #         if isinstance(authors[0], str):
    #             name, email = authors[0].split("<")
    #             name = name.strip()
    #             email = email.strip(">")
    #             uv_toml["project"]["authors"] = [
    #                 {"name": name, "email": email},
    #                 {"name": "test", "email": "test@email.com"},
    #             ]
    uv_toml["project"]["authors"] = [
        '{"name": "example", "email": "example@email.com"}'
    ]


def python_version(uv_toml: dict):
    # check specific python version
    uv_toml["project"]["requires-python"] = version_conversion(
        uv_toml["project"]["dependencies"]["python"]
    )
    del uv_toml["project"]["dependencies"]


def dev_dependencies(uv_toml: dict):
    # dev dependencies
    if (
        deps := uv_toml["project"]
        .get("group", {})
        .get("dev", {})
        .get("dependencies", {})
    ):
        if uv_toml["project"].get("group", {}).get("dev", {}).get("optional", ""):
            print("The Dev optional flag is ignored. You'll have to take care of this!")

        uv_deps = []

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
        uv_toml["dependency-groups"] = {"dev": uv_deps}
        del uv_toml["project"]["group"]["dev"]


def tool(uv_toml: dict, pyproject_data: dict):
    # deal with other tools
    for tool, data in pyproject_data["tool"].items():
        if tool == "poetry":
            continue
        uv_toml["tool"][tool] = data


def main():
    # test
    # c = Path("pyproject.toml")
    # with c.open("r") as f:
    #     current = toml.load(f)
    # print()
    ###
    uv_toml = {"project": {}, "tool": {}}
    # Parse pyproject.toml

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

    uv_toml["project"] = pyproject_data["tool"]["poetry"]
    authors(uv_toml)
    python_version(uv_toml)
    dev_dependencies(uv_toml)
    tool(uv_toml, pyproject_data)
    if "group" in uv_toml["project"]:
        del uv_toml["project"]["group"]

    if not dry_run:
        project_file.rename(backup_file)

    with output_file.open("w") as f:
        toml.dump(uv_toml, f)

    print("Actions required:")
    print("* Change the authors, it requires a list of dicts with name and email.")
    print("\t* https://packaging.python.org/en/latest/guides/writing-pyproject-toml/")
    print("* if any '\\n' or '\\t' are found, make it pretty yourself.")


if __name__ == "__main__":
    main()
