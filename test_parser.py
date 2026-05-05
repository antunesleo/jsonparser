import pytest

from parser import parsestr, ParsingError


@pytest.mark.parametrize(
    "json_str",
    ["{}", " {}", " {}", " { } "]
)
def test_parse_empty_object(json_str):
    assert parsestr(json_str) == {}


@pytest.mark.parametrize(
    "wrong_json",
    ["{", "}", "{}}", "{{}", "{{{}", "{{}}"]
)
def test_parse_wrong_empty_object(wrong_json):
    with pytest.raises(ParsingError):
        assert parsestr(wrong_json) == {}
