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
        parsestr(wrong_json)


@pytest.mark.parametrize(
    "json_str",
    ["null", " null", "null ", " null "]
)
def test_parse_null(json_str):
    assert parsestr(json_str) == None

@pytest.mark.parametrize(
    "wrong_json",
    ["n ull", " nu ll", "NULL ", "none", "\{null\}"]
)
def test_parse_null(wrong_json):
    with pytest.raises(ParsingError):
        parsestr(wrong_json)
