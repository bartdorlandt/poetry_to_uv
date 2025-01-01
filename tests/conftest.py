from pathlib import Path

import pytest
import tomlkit


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
    new_toml = tomlkit.document()
    new_toml["project"] = tomlkit.table()
    return new_toml


@pytest.fixture
def toml_obj():
    def inner(filepath: str):
        return tomlkit.loads(Path(filepath).read_text())

    return inner


@pytest.fixture
def expected_project_base():
    return {
        "project": {
            "name": "name of the project",
            "version": "0.1.0",
            "description": "A description",
            "authors": ["another <email@domain.nl>", "<some@email.nl>", "user"],
            "maintainers": ["another <email@domain.nl>", "<some@email.nl>", "user"],
            "license": "LICENSE",
            "readme": "README.md",
            "requires-python": ">=3.12",
            "keywords": ["packaging", "poetry"],
            "classifiers": [
                "Topic :: Software Development :: Build Tools",
                "Topic :: Software Development :: Libraries :: Python Modules",
            ],
            "urls": {"Bug Tracker": "https://github.com/python-poetry/poetry/issues"},
            "scripts": {"script_name": "dir.file:app"},
            "dependencies": {
                "python": "^3.12",
                "pytest": "*",
                "pytest-cov": "*",
                "pytest-mock": "*",
                "ruff": "*",
                "jira": "^3.8.0",
            },
        }
    }
