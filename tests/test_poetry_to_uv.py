import pytest

import poetry_to_uv


@pytest.mark.parametrize(
    "name, email",
    [
        (["firstname lastname", "name@domain.nl"]),
        (["another one", "just@checking.com"]),
    ],
)
def test_authors(name, email):
    authors = [f"{name} <{email}>"]
    in_dict = {"project": {"authors": authors}}
    expected = {"project": {"authors": f"[{{'name' = '{name}', 'email' = '{email}'}}]"}}
    poetry_to_uv.authors(in_dict)
    assert in_dict == expected


def test_authors_empty():
    in_dict = {"project": {}}
    expected = {
        "project": {
            "authors": "[{{'name' = 'example', 'email' = 'example@email.com'}}]"
        }
    }
    poetry_to_uv.authors(in_dict)
    assert in_dict == expected


def test_dependencies():
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
    poetry_to_uv.dependencies(in_dict)
    assert in_dict == expected


def test_dev_dependencies():
    in_dict = {
        "project": {
            "group": {
                "dev": {
                    "dependencies": {
                        "pytest": "*",
                        "pytest-cov": "*",
                        "jira": "^3.8.0",
                    }
                }
            }
        }
    }
    expected = {
        "project": {},
        "dependency-groups": {"dev": ["pytest", "pytest-cov", "jira>=3.8.0"]},
    }
    poetry_to_uv.dev_dependencies(in_dict)
    assert in_dict == expected
