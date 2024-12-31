from pathlib import Path

import pytest
import tomlkit

import poetry_to_uv


@pytest.fixture
def read_poetry_toml_as_text():
    f = Path("tests/files/poetry_pyproject.toml")
    return f.read_text()


@pytest.fixture
def org_toml():
    return {
        "tool": {
            "poetry": {
                "dependencies": {
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
def read_poetry_toml_as_object(read_poetry_toml_as_text):
    return tomlkit.loads(read_poetry_toml_as_text)


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
    in_dict = {key: authors}
    expected = {key: [{"name": name, "email": email}]}
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
    in_dict = {"authors": authors}
    expected = {"authors": author_string}
    poetry_to_uv.authors_maintainers(in_dict)
    assert in_dict == expected


def test_dependencies(org_toml):
    in_dict = {
        "project": {
            "dependencies": {
                "pytest": "*",
                "pytest-cov": "*",
                "jira": "^3.8.0",
            }
        }
    }
    expected = {"project": {"dependencies": ["pytest", "pytest-cov", "jira>=3.8.0"]}}
    poetry_to_uv.dependencies(in_dict, org_toml)
    assert in_dict == expected


def test_optional_dependencies(org_toml_optional):
    in_dict = {
        "project": {
            "dependencies": {
                "pytest": "*",
                "pytest-cov": "*",
            },
        }
    }
    expected = {
        "project": {
            "dependencies": ["pytest", "pytest-cov"],
            "optional-dependencies": {"JIRA": ["jira>=3.8.0"]},
        }
    }
    poetry_to_uv.dependencies(in_dict, org_toml_optional)
    assert in_dict == expected


def test_dev_dependencies(org_toml):
    in_dict = {"project": {}}
    expected = {
        "project": {},
        "dependency-groups": {"dev": ["mypy>=1.0.1"]},
    }
    poetry_to_uv.dev_dependencies(in_dict, org_toml)
    assert in_dict == expected


{"project": {"license": "MIT"}}
{"project": {"license": {"text": "MIT"}}}


def test_project_license():
    in_dict = {"license": "MIT"}
    expected = {"license": {"text": "MIT"}}
    poetry_to_uv.project_license(in_dict, Path())
    assert in_dict == expected


def test_project_license_file(tmp_path):
    license_name = "license_file_name"
    in_dict = {"license": license_name}
    tmp_path.joinpath(license_name).touch()
    expected = {"license": {"file": license_name}}
    poetry_to_uv.project_license(in_dict, tmp_path)
    assert in_dict == expected


def test_build_system(read_poetry_toml_as_object):
    in_dict = {
        "build-system": read_poetry_toml_as_object["build-system"],
    }
    expected = {
        "build-system": {
            "requires": ["hatchling"],
            "build-backend": "hatchling.build",
        }
    }
    poetry_to_uv.build_system(in_dict, in_dict)
    assert in_dict == expected
