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
    ["n ull", " nu ll", "NULL ", "none", "{null}"]
)
def test_parse_wrong_null(wrong_json):
    with pytest.raises(ParsingError):
        parsestr(wrong_json)


@pytest.mark.parametrize(
    "json_str,expected",
    [("true", True), (" true", True), ("false", False), ("false ", False)]
)
def test_parse_boolean(json_str, expected):
    assert parsestr(json_str) == expected

@pytest.mark.parametrize(
    "wrong_json",
    ["True", "False", "tr ue", "fa lse"]
)
def test_parse_wrong_boolean(wrong_json):
    with pytest.raises(ParsingError):
        parsestr(wrong_json)


@pytest.mark.parametrize(
    "json_str,expected",
    [("1", 1), (" 0", 0), ("150", 150), ("128.23 ", 128.23), ("120e2", 12000)]
)
def test_parse_number(json_str, expected):
    assert parsestr(json_str) == expected
