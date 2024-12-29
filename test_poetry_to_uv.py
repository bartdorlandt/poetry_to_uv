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
        "project": {"authors": [{"name": "example", "email": "example@email.com"}]}
    }
    poetry_to_uv.authors(in_dict)
    assert in_dict == expected
