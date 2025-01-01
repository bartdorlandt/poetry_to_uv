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
    return {"project": {}}


@pytest.fixture
def toml_obj():
    def inner(filepath: str):
        return tomlkit.loads(Path(filepath).read_text())

    return inner
