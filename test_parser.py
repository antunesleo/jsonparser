import pytest

from parser import parsestr, ParsingError


@pytest.mark.parametrize(
    "json_str",
    [
        "{}",
        " {}",
        " {} ",
        " { } ",
        "\t{}\n",
        "{\t}",
        "\r\n{ }\r\n",
        " \t\n\r{}\r\n\t ",
        "{\n}",
    ]
)
def test_parse_empty_object(json_str):
    assert parsestr(json_str) == {}


@pytest.mark.parametrize(
    "wrong_json",
    [
        "{",
        "}",
        "{}}",
        "{{}",
        "{{{}",
        "{{}}",
        "",
        "   ",
        "{a}",
        "{,}",
        "{}{}",
    ]
)
def test_parse_wrong_empty_object(wrong_json):
    with pytest.raises(ParsingError):
        parsestr(wrong_json)


@pytest.mark.parametrize(
    "json_str",
    [
        "null",
        " null",
        "null ",
        " null ",
        "\tnull",
        "null\n",
        "\r\nnull\r\n",
        " \t\nnull\r\n ",
    ]
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
        "",
        "Null",
        "nULL",
        "nullnull",
        "null null",
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
        (" true ", True),
        (" false ", False),
        ("\rtrue\r", True),
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
        "TRUE",
        "FALSE",
        "truefalse",
        "true false",
        "fals e",
        "trues",
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
        ("0", 0),
        ("0.0", 0.0),
        ("0e0", 0.0),
        ("-0.5", -0.5),
        ("-1.5e2", -150.0),
        ("-1.5e-2", -0.015),
        ("1.0", 1.0),
        ("0.001", 0.001),
        ("1000000", 1000000),
        ("9999999999", 9999999999),
        ("1E0", 1.0),
        ("-0.0", -0.0),
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
        "+1",
        "--1",
        "1..5",
        "e5",
        "1e1.5",
        "0x10",
        "-.5",
        "1e--1",
        ".",
        "1.e5",
    ]
)
def test_parse_wrong_number(wrong_json):
    with pytest.raises(ParsingError):
        parsestr(wrong_json)


@pytest.mark.parametrize(
    "json_str,expected",
    [
        ('"hello"', "hello"),
        ('""', ""),
        (' "hello"', "hello"),
        ('"hello" ', "hello"),
        (' "hello" ', "hello"),
        ('\t"hello"\n', "hello"),
        ('"hello world"', "hello world"),
        ('"123"', "123"),
        ('"true"', "true"),
        ('"null"', "null"),
        ('"with : colon and , comma"', "with : colon and , comma"),
        ('"a"', "a"),
        ('" "', " "),
        ('"日本語"', "日本語"),
        ('"!@#$%^&*()"', "!@#$%^&*()"),
        ('"a/b/c"', "a/b/c"),
        ('"{not an object}"', "{not an object}"),
        ('"[not a list]"', "[not a list]"),
        ('"123.45"', "123.45"),
        ('"   "', "   "),
    ]
)
def test_parse_string(json_str, expected):
    assert parsestr(json_str) == expected


@pytest.mark.parametrize(
    "wrong_json",
    [
        '"',
        '"hello',
        'hello"',
        'hello',
        "'hello'",
        '"hello" garbage',
        '""x',
        '"""',
        '"abc',
        '""""',
        '"a"" b"',
    ]
)
def test_parse_wrong_string(wrong_json):
    with pytest.raises(ParsingError):
        parsestr(wrong_json)


@pytest.mark.parametrize(
    "json_str, expected",
    [
        ('{"field": "value"}', {"field": "value"}),
        ('{"field": 1}', {"field": 1}),
        ('{"field": 1.5}', {"field": 1.5}),
        ('{"field": null}', {"field": None}),
        ('{"field": false}', {"field": False}),
        ('{"field1": true, "field2": "value"}', {"field1": True, "field2": "value"}),
        ('{ "field" : 1 }', {"field": 1}),
        ('{"a": 1, "b": 2, "c": 3}', {"a": 1, "b": 2, "c": 3}),
        ('{"k": -1.5e2}', {"k": -150.0}),
        ('{"k": []}', {"k": []}),
        ('{"k": {}}', {"k": {}}),
        ('{"": "empty key"}', {"": "empty key"}),
        ('{"k": ""}', {"k": ""}),
        ('{\n  "name": "test",\n  "value": 42\n}', {"name": "test", "value": 42}),
        ('{"a":1,"b":2}', {"a": 1, "b": 2}),
        ('{"a": true, "b": false, "c": null}', {"a": True, "b": False, "c": None}),
    ]
)
def test_parse_shallow_object(json_str, expected):
    assert parsestr(json_str) == expected


@pytest.mark.parametrize(
    "wrong_json",
    [
        '{"a": }',
        '{"a" 1}',
        '{"a": 1 "b": 2}',
        '{"a": 1,}',
        '{,"a": 1}',
        '{a: 1}',
        '{"a": 1',
        '{"a": 1}garbage',
        '{"a"}',
        '{:}',
        '{"a": 1, "b"}',
        '{"a":}',
        '{1: "a"}',
        '{"a": 1,, "b": 2}',
        '{"a": 1; "b": 2}',
        '{"a"::1}',
        '{"a": 1}{"b": 2}',
    ]
)
def test_parse_wrong_object(wrong_json):
    with pytest.raises(ParsingError):
        parsestr(wrong_json)


@pytest.mark.parametrize(
    "json_str,expected",
    [
        ("[]", []),
        (" [] ", []),
        ("\t[]\n", []),
        ("[1]", [1]),
        ("[1, 2, 3]", [1, 2, 3]),
        (" [ 1 , 2 , 3 ] ", [1, 2, 3]),
        ("[null, true, false]", [None, True, False]),
        ('["a", "b"]', ["a", "b"]),
        ('[1, "two", 3.5, null]', [1, "two", 3.5, None]),
        ("[[1, 2], [3, 4]]", [[1, 2], [3, 4]]),
        ('[{"k": 1}]', [{"k": 1}]),
        ("[[]]", [[]]),
        ("[[[]]]", [[[]]]),
        ("[{}]", [{}]),
        ("[{}, {}]", [{}, {}]),
        ("[-1]", [-1]),
        ("[-1.5e2]", [-150.0]),
        ("[1,2,3]", [1, 2, 3]),
        ('[""]', [""]),
        ("[null]", [None]),
        ("[[1], [2], [3]]", [[1], [2], [3]]),
        ('[\n  1,\n  2\n]', [1, 2]),
    ]
)
def test_parse_list(json_str, expected):
    assert parsestr(json_str) == expected


@pytest.mark.parametrize(
    "wrong_json",
    [
        "[",
        "]",
        "[,]",
        "[1,]",
        "[,1]",
        "[1 2]",
        "[1, 2",
        "1, 2]",
        "[]x",
        "[1] [2]",
        "[[]",
        "[]]",
        "[1, 2; 3]",
        "[1,, 2]",
        "[1 ,, 2]",
        "[1, [2]",
    ]
)
def test_parse_wrong_list(wrong_json):
    with pytest.raises(ParsingError):
        parsestr(wrong_json)


@pytest.mark.parametrize(
    "json_str,expected",
    [
        # Deeply nested objects
        ('{"a": {"b": {"c": {"d": 1}}}}', {"a": {"b": {"c": {"d": 1}}}}),
        # Deeply nested arrays
        ("[[[[1]]]]", [[[[1]]]]),
        # Object with array values
        ('{"items": [1, 2, 3]}', {"items": [1, 2, 3]}),
        # Array of objects
        ('[{"a": 1}, {"a": 2}]', [{"a": 1}, {"a": 2}]),
        # Mixed deep nesting
        (
            '{"users": [{"id": 1, "tags": ["a", "b"]}, {"id": 2, "tags": []}]}',
            {"users": [{"id": 1, "tags": ["a", "b"]}, {"id": 2, "tags": []}]},
        ),
        # Object containing array of objects with arrays
        (
            '{"data": [{"k": [1, 2]}, {"k": [3, 4]}]}',
            {"data": [{"k": [1, 2]}, {"k": [3, 4]}]},
        ),
        # All primitive types in one object
        (
            '{"s": "x", "n": 1, "f": 1.5, "b": true, "z": null}',
            {"s": "x", "n": 1, "f": 1.5, "b": True, "z": None},
        ),
        # All value types in one array
        (
            '[null, true, false, 0, 1.5, "x", [], {}]',
            [None, True, False, 0, 1.5, "x", [], {}],
        ),
        # Realistic JSON with formatting
        (
            '{\n  "name": "Alice",\n  "age": 30,\n  "items": [\n    1,\n    2,\n    3\n  ]\n}',
            {"name": "Alice", "age": 30, "items": [1, 2, 3]},
        ),
        # Empty containers nested
        ("[[], [], []]", [[], [], []]),
        ('{"a": {}, "b": []}', {"a": {}, "b": []}),
        # Deeply nested mixed
        (
            '{"a": [{"b": [{"c": [1, 2, 3]}]}]}',
            {"a": [{"b": [{"c": [1, 2, 3]}]}]},
        ),
        # Whitespace stress test
        (
            '\t\n  { "a" : [ 1 , 2 , { "b" : null } ] }\n\t',
            {"a": [1, 2, {"b": None}]},
        ),
    ]
)
def test_parse_complex(json_str, expected):
    assert parsestr(json_str) == expected
