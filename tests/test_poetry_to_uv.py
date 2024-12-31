from pathlib import Path

import pytest
import toml

import poetry_to_uv


@pytest.fixture
def read_poetry_toml_as_text():
    f = Path("tests/files/poetry_pyproject.toml")
    return f.read_text()


@pytest.fixture
def read_poetry_toml_as_object(read_poetry_toml_as_text):
    return toml.loads(read_poetry_toml_as_text)


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
    expected = {"project": {key: f'[{{name = "{name}", email = "{email}"}}]'}}
    poetry_to_uv.authors_maintainers(in_dict)
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
    poetry_to_uv.authors_maintainers(in_dict)
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
                "jira": {"version": "^3.8.0", "optional": True},
            },
            "extras": {"JIRA": ["jira"]},
        }
    }
    expected = {
        "project": {
            "dependencies": ["pytest", "pytest-cov"],
            "optional-dependencies": {"JIRA": ["jira>=3.8.0"]},
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
    result = poetry_to_uv.modify_authors_maintainers_line(in_txt, "authors")
    assert result == out_txt
    assert (
        poetry_to_uv.modify_authors_maintainers_line(result, "maintainers") == out_txt
    )


def test_modify_maintainers_line():
    in_txt = """[project]
name = "someproject"
version = "0.1.0"
description = "A project"
maintainers = "[{ name = \"First Last\", email = \"first@domain.nl\" }]"
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
maintainers = [{ name = "First Last", email = "first@domain.nl" }]
license = "LICENSE"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "jira>=3.8.0",
]
"""
    assert (
        poetry_to_uv.modify_authors_maintainers_line(in_txt, "maintainers") == out_txt
    )


def test_modify_authors_and_maintainers_line():
    in_txt = """[project]
name = "someproject"
version = "0.1.0"
description = "A project"
authors = "[{ name = \"First Last\", email = \"first@domain.nl\" }]"
maintainers = "[{ name = \"First Last\", email = \"first@domain.nl\" }]"
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
maintainers = [{ name = "First Last", email = "first@domain.nl" }]
license = "LICENSE"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "jira>=3.8.0",
]
"""
    result = poetry_to_uv.modify_authors_maintainers_line(in_txt, "authors")
    assert (
        poetry_to_uv.modify_authors_maintainers_line(result, "maintainers") == out_txt
    )


def test_modify_authors_and_maintainers_line_with_multiple_ids(
    read_poetry_toml_as_object,
):
    uv_toml = {"tool": {}, "project": read_poetry_toml_as_object["tool"]["poetry"]}
    poetry_to_uv.authors_maintainers(uv_toml)
    in_txt = toml.dumps(uv_toml)
    result = poetry_to_uv.modify_authors_maintainers_line(in_txt, "authors")
    result = poetry_to_uv.modify_authors_maintainers_line(result, "maintainers")
    obj = toml.loads(result)
    assert_accounts = [
        {"name": "another", "email": "email@domain.nl"},
        {"email": "some@email.nl"},
        {"name": "user"},
    ]
    # sourcery skip: no-loop-in-tests
    for account in assert_accounts:
        assert account in obj["project"]["authors"]
        assert account in obj["project"]["maintainers"]


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


def test_build_system(read_poetry_toml_as_object):
    in_dict = {
        "build-system": read_poetry_toml_as_object["build-system"],
    }
    expected = {
        "build-system": {
            "requires": ["poetry-core>=1.0.0"],
            "build-backend": "poetry.core.masonry.api",
        }
    }
    poetry_to_uv.blocks_as_is(in_dict, in_dict)
    assert in_dict == expected
