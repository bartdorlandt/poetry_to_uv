from pathlib import Path

import pytest

import poetry_to_uv


@pytest.fixture
def org_toml():
    return {
        "tool": {
            "poetry": {
                "dependencies": {
                    "python": "^3.12",
                    "pytest": "*",
                    "pytest-cov": "*",
                    "jira": "^3.8.0",
                },
                "group": {
                    "dev": {
                        "dependencies": {
                            "mypy": "^1.0.1",
                        }
                    }
                },
            }
        }
    }


@pytest.fixture
def org_toml_optional():
    return {
        "tool": {
            "poetry": {
                "dependencies": {
                    "pytest": "*",
                    "pytest-cov": "*",
                    "jira": {"version": "^3.8.0", "optional": True},
                },
                "extras": {"JIRA": ["jira"]},
            }
        }
    }


@pytest.fixture
def pyproject_empty_base():
    return {"project": {}}


@pytest.mark.parametrize(
    "key, value",
    [
        ("^3.6", ">=3.6"),
        ("*", ""),
        ("^1.2.3", ">=1.2.3"),
    ],
)
def test_version_conversion(key, value):
    assert poetry_to_uv.version_conversion(key) == value


@pytest.mark.parametrize(
    "key, name, email",
    [
        (["authors", "firstname lastname", "name@domain.nl"]),
        (["authors", "another one", "just@checking.com"]),
        (["maintainers", "firstname lastname", "name@domain.nl"]),
        (["maintainers", "another one", "just@checking.com"]),
    ],
)
def test_authors_maintainers(key, name, email):
    authors = [f"{name} <{email}>"]
    in_dict = {"project": {key: authors}}
    expected = {"project": {key: [{"name": name, "email": email}]}}
    poetry_to_uv.authors_maintainers(in_dict)
    assert in_dict == expected


@pytest.mark.parametrize(
    "authors, author_string",
    [
        (
            ["First Last <first@domain2.nl>", "another <email@domain.nl>"],
            [
                {"name": "First Last", "email": "first@domain2.nl"},
                {"name": "another", "email": "email@domain.nl"},
            ],
        ),
        (
            ["First Last", "<email@domain.nl>"],
            [{"name": "First Last"}, {"email": "email@domain.nl"}],
        ),
        (
            ["First Last <first@domain2.nl>", "<email@domain.nl>", "First Last"],
            [
                {"name": "First Last", "email": "first@domain2.nl"},
                {"email": "email@domain.nl"},
                {"name": "First Last"},
            ],
        ),
    ],
)
def test_multiple_authors(authors, author_string):
    in_dict = {"project": {"authors": authors}}
    expected = {"project": {"authors": author_string}}
    poetry_to_uv.authors_maintainers(in_dict)
    assert in_dict == expected


def test_no_python_in_deps(org_toml):
    deps = org_toml["tool"]["poetry"]["dependencies"]
    uv_deps = []
    poetry_to_uv.parse_packages(deps, uv_deps)
    assert "python" not in uv_deps


def test_dependencies(pyproject_empty_base, org_toml):
    expected = {"project": {"dependencies": ["pytest", "pytest-cov", "jira>=3.8.0"]}}
    poetry_to_uv.dependencies(pyproject_empty_base, org_toml)
    assert pyproject_empty_base == expected


def test_optional_dependencies(pyproject_empty_base, org_toml_optional):
    expected = {
        "project": {
            "dependencies": ["pytest", "pytest-cov"],
            "optional-dependencies": {"JIRA": ["jira>=3.8.0"]},
        }
    }
    poetry_to_uv.dependencies(pyproject_empty_base, org_toml_optional)
    assert pyproject_empty_base == expected


def test_dev_dependencies(pyproject_empty_base, org_toml):
    expected = {
        "project": {},
        "dependency-groups": {"dev": ["mypy>=1.0.1"]},
    }
    poetry_to_uv.group_dependencies(pyproject_empty_base, org_toml)
    assert pyproject_empty_base == expected


def test_doc_dependencies(pyproject_empty_base, org_toml):
    org_toml["tool"]["poetry"]["group"]["doc"] = {"dependencies": {"mkdocs": "*"}}
    expected = {
        "project": {},
        "dependency-groups": {"dev": ["mypy>=1.0.1"], "doc": ["mkdocs"]},
    }
    poetry_to_uv.group_dependencies(pyproject_empty_base, org_toml)
    assert pyproject_empty_base == expected


def test_project_license():
    in_dict = {"project": {"license": "MIT"}}
    expected = {"project": {"license": {"text": "MIT"}}}
    poetry_to_uv.project_license(in_dict, Path())
    assert in_dict == expected


def test_project_license_file(tmp_path):
    license_name = "license_file_name"
    in_dict = {"project": {"license": license_name}}
    tmp_path.joinpath(license_name).touch()
    expected = {"project": {"license": {"file": license_name}}}
    poetry_to_uv.project_license(in_dict, tmp_path)
    assert in_dict == expected


def test_build_system():
    in_dict = {
        "build-system": {
            "requires": ["poetry-core>=1.0.0"],
            "build-backend": "poetry.core.masonry.api",
        }
    }
    expected = {
        "build-system": {
            "requires": ["hatchling"],
            "build-backend": "hatchling.build",
        }
    }
    poetry_to_uv.build_system(in_dict, in_dict)
    assert in_dict == expected
