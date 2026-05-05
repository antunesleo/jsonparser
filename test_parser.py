import pytest

from parser import parsestr, ParsingError


@pytest.mark.parametrize(
    "json_str",
    ["{}", " {}", " {}", " { } ", "\t{}\n", "{\t}", "\r\n{ }\r\n"]
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
    ["null", " null", "null ", " null ", "\tnull", "null\n", "\r\nnull\r\n"]
)
def test_parse_null(json_str):
    assert parsestr(json_str) == None

@pytest.mark.parametrize(
    "wrong_json",
    [
        "n ull",
        " nu ll",
        "NULL ",
        "none",
        "{null}",
        "nullx",
        "null garbage",
        "nul",
    ]
)
def test_parse_wrong_null(wrong_json):
    with pytest.raises(ParsingError):
        parsestr(wrong_json)


@pytest.mark.parametrize(
    "json_str,expected",
    [
        ("true", True),
        (" true", True),
        ("false", False),
        ("false ", False),
        ("\ttrue\n", True),
        ("\r\nfalse\r\n", False),
    ]
)
def test_parse_boolean(json_str, expected):
    assert parsestr(json_str) == expected

@pytest.mark.parametrize(
    "wrong_json",
    [
        "True",
        "False",
        "tr ue",
        "fa lse",
        "truex",
        "falsex",
        "true garbage",
        "tru",
        "fals",
    ]
)
def test_parse_wrong_boolean(wrong_json):
    with pytest.raises(ParsingError):
        parsestr(wrong_json)


@pytest.mark.parametrize(
    "json_str,expected",
    [
        ("1", 1),
        (" 0", 0),
        (" 150 ", 150),
        (" 128.23 ", 128.23),
        ("120e2", 12000),
        ("1e+10", 1e10),
        ("1E5", 1e5),
        ("1.5e-3", 1.5e-3),
        ("-0", 0),
        ("-42", -42),
        ("0.5", 0.5),
        ("\t42\n", 42),
    ]
)
def test_parse_number(json_str, expected):
    assert parsestr(json_str) == expected


@pytest.mark.parametrize(
    "wrong_json",
    [
        "1 50",
        "50*43",
        ".23",
        "45.45.45",
        "45,45.45",
        "45e2e2",
        "007",
        "01",
        "-",
        "1.",
        "1e",
        "1e+",
    ]
)
def test_parse_wrong_number(wrong_json):
    with pytest.raises(ParsingError):
        parsestr(wrong_json)


# @pytest.mark.parametrize(
#     "json_str, expected",
#     [
#         ('{"field": "value"}', {"field": "value"}), 
#         ('{"field": 1}', {"field": 1}),
#         ('{"field": 1.5}', {"field": 1.5}),
#         ('{"field": null}', {"field": None}),
#         ('{"field": false}', {"field": False}),
#         ('{"field1": true, "field2": "value"}', {"field1": True, "field2": "value"})
#     ]
# )
# def test_parse_shallow_object(json_str, expected):
#     assert parsestr(json_str) == expected
