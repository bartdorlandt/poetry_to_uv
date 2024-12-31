#!/usr/bin/env python
import argparse
import re
from pathlib import Path

import tomlkit as tk

gt_version = re.compile(r"\^(\d.*)")


def argparser() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="poetry_to_uv",
        description="Poetry to Uv pyproject conversion",
        epilog="It will move the original pyproject.toml to pyproject.toml.org",
    )
    parser.add_argument("filename")
    parser.add_argument(
        "-n",
        action="store_true",
        help="Do not modify pyproject.toml, instead create pyproject_temp_uv.toml",
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


def authors_maintainers(project: tk.table):
    user_email = re.compile(r"^([\w ]+) <([\w@.]+)>$")
    only_email = re.compile(r"^<([\w@.]+)>$")
    only_user = re.compile(r"^([\w ]+)$")

    for key in ("authors", "maintainers"):
        if authors := project.get(key):
            if isinstance(authors, list):
                new_authors = tk.array()
                for author in authors:
                    if found := user_email.match(author):
                        name, email = found.groups()
                        tb = tk.inline_table().add("name", name).add("email", email)
                        new_authors.add_line(tb)
                    elif found := only_email.match(author):
                        email = found[1]
                        new_authors.add_line(tk.inline_table().add("email", email))
                    elif found := only_user.match(author):
                        name = found[1]
                        new_authors.add_line(tk.inline_table().add("name", name))
                    else:
                        print(f"Unknown author {key} format: {author}")

                new_authors.add_line(indent="")
                project[key] = new_authors


def python_version(project: tk.table):
    # check specific python version
    if version := project.get("requires-python"):
        project["requires-python"] = version_conversion(version)


def parse_packages(deps: dict, uv_deps: list[str], uv_deps_optional=None):
    if uv_deps_optional is None:
        uv_deps_optional = {}
    for name, version in deps.items():
        extra = ""
        if name == "python":
            continue

        if isinstance(version, dict):
            # deal with extras
            if e := version.get("extras"):
                v = version["version"]
                for i in e:
                    extra = f"[{i}]"
                    uv_deps.append(f"{name}{extra}{version_conversion(v)}")
                continue
            if version.get("optional"):
                uv_deps_optional[name] = version_conversion(version["version"])
                continue

        uv_deps.append(f"{name}{extra}{version_conversion(version)}")


def dev_dependencies(new_toml: tk.TOMLDocument, org_toml: tk.TOMLDocument) -> None:
    if not (
        deps := org_toml["tool"]["poetry"]
        .get("group", {})
        .get("dev", {})
        .get("dependencies", {})
    ):
        return
    if org_toml["tool"]["poetry"].get("group", {}).get("dev", {}).get("optional", ""):
        print("The Dev optional flag is ignored. You'll have to take care of this!")

    uv_deps = []
    parse_packages(deps, uv_deps)
    dep_groups = tk.table()
    dep_groups.add("dev", uv_deps)
    new_toml["dependency-groups"] = dep_groups


def dependencies(new_toml: tk.TOMLDocument, org_toml: tk.TOMLDocument) -> None:
    if not (deps := org_toml["tool"]["poetry"].get("dependencies", {})):
        return
    uv_deps = []
    uv_deps_optional = {}

    parse_packages(deps, uv_deps, uv_deps_optional)
    new_toml["project"]["dependencies"] = tk.array()
    if uv_deps:
        for x in uv_deps:
            new_toml["project"]["dependencies"].add_line(x)
        new_toml["project"]["dependencies"].add_line(indent="")

    if uv_deps_optional:
        optional_deps = {
            extra: [f"{x}{uv_deps_optional[x]}" for x in deps]
            for extra, deps in org_toml["tool"]["poetry"].pop("extras", {}).items()
        }
        new_toml["project"]["optional-dependencies"] = optional_deps


def tools(new_toml: tk.TOMLDocument, org_toml: tk.TOMLDocument):
    if org_toml["tool"]:
        new_toml["tool"] = tk.table()
        for tool, data in org_toml["tool"].items():
            if tool == "poetry":
                continue
            new_toml["tool"][tool] = data


def build_system(new_toml: tk.TOMLDocument, org_toml: tk.TOMLDocument):
    if build := org_toml.get("build-system"):
        new_toml["build-system"] = org_toml["build-system"]
        if "poetry" in build.get("build-backend"):
            print("Poetry build system detected. Replaced with hatchling")
            new_toml["build-system"]["requires"] = ["hatchling"]
            new_toml["build-system"]["build-backend"] = "hatchling.build"


def project_base(project: tk.table, org_toml: tk.TOMLDocument):
    project.add("name", org_toml["tool"]["poetry"]["name"])
    project.add("version", org_toml["tool"]["poetry"]["version"])
    if description := org_toml["tool"]["poetry"].get("description"):
        project.add("description", description)
    if authors := org_toml["tool"]["poetry"].get("authors"):
        project.add("authors", authors)
    if maintainers := org_toml["tool"]["poetry"].get("maintainers"):
        project.add("maintainers", maintainers)
    if license := org_toml["tool"]["poetry"].get("license"):
        project.add("license", license)
    if readme := org_toml["tool"]["poetry"].get("readme"):
        project.add("readme", readme)
    if requirespython := org_toml["tool"]["poetry"].get("requires-python"):
        project.add("requires-python", requirespython)
    elif (
        requirespython := org_toml["tool"]["poetry"]
        .get("dependencies", {})
        .get("python")
    ):
        project.add("requires-python", requirespython)
    if keywords := org_toml["tool"]["poetry"].get("keywords"):
        project.add("keywords", keywords)
    if classifiers := org_toml["tool"]["poetry"].get("classifiers"):
        project.add("classifiers", classifiers)
    if urls := org_toml["tool"]["poetry"].get("urls"):
        project.add("urls", urls)

    if scripts := org_toml["tool"]["poetry"].get("scripts"):
        project.add("scripts", scripts)

    if dependencies := org_toml["tool"]["poetry"].get("dependencies"):
        project.add("dependencies", dependencies)


def project_license(project: tk.table, project_dir: Path):
    if license := project.get("license"):
        if project_dir.joinpath(license).exists():
            project["license"] = tk.inline_table().add("file", license)
        else:
            project["license"] = tk.inline_table().add("text", license)


def poetry_section_specific(
    new_toml: tk.TOMLDocument, org_toml: tk.TOMLDocument, dir: Path
):
    project = new_toml["project"]
    project_base(project, org_toml)
    project_license(project, dir)
    python_version(project)
    authors_maintainers(project)
    dev_dependencies(new_toml, org_toml)
    dependencies(new_toml, org_toml)


def main():
    args = argparser()
    project_file = Path(args.filename)
    org_toml = tk.loads(project_file.read_text())
    if not org_toml.get("tool", {}).get("poetry"):
        print("Poetry section not found, are you certain this is a poetry project?")
        return

    dry_run = args.n
    project_dir = project_file.parent
    backup_file = project_dir / f"{project_file.name}.org"
    if dry_run:
        output_file = Path(project_dir / "pyproject_temp_uv.toml")
        print(f"Dry_run enabled. Output file: {output_file}")
    else:
        print(f"Replacing {project_file}\nBackup file : {backup_file}")
        output_file = project_file

    new_toml = tk.document()
    new_toml.add(tk.comment("This has been generated by poetry_to_uv.py."))
    new_toml.add(tk.nl())
    new_toml["project"] = tk.table()

    poetry_section_specific(new_toml, org_toml, dir=project_dir)
    build_system(new_toml, org_toml)
    tools(new_toml, org_toml)

    if not dry_run:
        project_file.rename(backup_file)

    output_file.write_text(tk.dumps(new_toml))

    print(
        "* Information on pyproject.toml: https://packaging.python.org/en/latest/guides/writing-pyproject-toml/"
    )


if __name__ == "__main__":
    main()
