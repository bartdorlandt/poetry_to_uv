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
    expected = {"project": {"authors": f'[{{name = "{name}", email = "{email}"}}]'}}
    poetry_to_uv.authors(in_dict)
    assert in_dict == expected


def test_authors_empty():
    in_dict = {"project": {}}
    expected = {
        "project": {"authors": '[{name = "example", email = "example@email.com"}]'}
    }
    poetry_to_uv.authors(in_dict)
    assert in_dict == expected


@pytest.mark.parametrize(
    "authors, author_string",
    [
        (
            ["First Last <first@domain2.nl>", "another <email@domain.nl>"],
            '[{name = "First Last", email = "first@domain2.nl"}, {name = "another", email = "email@domain.nl"}]',
        ),
        (
            ["First Last", "<email@domain.nl>"],
            '[{name = "First Last"}, {email = "email@domain.nl"}]',
        ),
        (
            ["First Last <first@domain2.nl>", "<email@domain.nl>", "First Last"],
            '[{name = "First Last", email = "first@domain2.nl"}, {email = "email@domain.nl"}, {name = "First Last"}]',
        ),
    ],
)
def test_multiple_authors(authors, author_string):
    in_dict = {"project": {"authors": authors}}
    expected = {"project": {"authors": author_string}}
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


def test_optional_dependencies():
    in_dict = {
        "project": {
            "dependencies": {
                "pytest": "*",
                "pytest-cov": "*",
                "jira": {"version": "^3.8.0", "optional": True}
            },
            "extras": {
                "JIRA": ["jira"]
            }
        }
    }
    expected= {
        "project": {
            "dependencies": ["pytest", "pytest-cov"],
            "optional-dependencies": {"JIRA": ["jira>=3.8.0"]}
        }
    }
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


def test_modify_authors_line():
    in_txt = """[project]
name = "someproject"
version = "0.1.0"
description = "A project"
authors = "[{ name = \"First Last\", email = \"first@domain.nl\" }]"
license = "LICENSE"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "jira>=3.8.0",
]
"""
    out_txt = """[project]
name = "someproject"
version = "0.1.0"
description = "A project"
authors = [{ name = "First Last", email = "first@domain.nl" }]
license = "LICENSE"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "jira>=3.8.0",
]
"""
    assert poetry_to_uv.modify_authors_line(in_txt) == out_txt


@pytest.mark.parametrize(
    "author_string",
    [
        '[{ name = "First Last", email = "first@domain.nl" }, { name = "Name", email = "name@domain.nl" }]',
        '[{ email = "first@domain.nl" }, { name = "Name"}]',
    ],
)
def test_modify_multiple_authors_line(author_string):
    in_txt = f"""[project]
name = "someproject"
version = "0.1.0"
description = "A project"
authors = "{author_string}"
license = "LICENSE"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "jira>=3.8.0",
]
"""
    out_txt = f"""[project]
name = "someproject"
version = "0.1.0"
description = "A project"
authors = {author_string}
license = "LICENSE"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "jira>=3.8.0",
]
"""
    assert poetry_to_uv.modify_authors_line(in_txt) == out_txt


def test_project_license():
    in_dict = {
        "project": {
            "license": "MIT"
        }
    }
    expected= {
        "project": {
            "license": {"text": "MIT"}
        }
    }
    poetry_to_uv.project_license(in_dict)
    assert in_dict == expected
