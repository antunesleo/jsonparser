import pytest

from astparser import ParsingError, Token, TokenType, tokenize


def T(type, value=None):
    return Token(type, value)


LB = T(TokenType.LBRACE)
RB = T(TokenType.RBRACE)
LBK = T(TokenType.LBRACKET)
RBK = T(TokenType.RBRACKET)
COLON = T(TokenType.COLON)
COMMA = T(TokenType.COMMA)


def STR(v):
    return T(TokenType.STRING, v)


def NUM(v):
    return T(TokenType.NUMBER, v)


def BOOL(v):
    return T(TokenType.BOOL, v)


NULL = T(TokenType.NULL, None)


# --- structural tokens --------------------------------------------------------

@pytest.mark.parametrize("s,expected", [
    ("{}", [LB, RB]),
    ("[]", [LBK, RBK]),
    ("{{}}", [LB, LB, RB, RB]),
    ("[[]]", [LBK, LBK, RBK, RBK]),
    ("{[]}", [LB, LBK, RBK, RB]),
    (",:", [COMMA, COLON]),
    ("", []),
    ("   ", []),
])
def test_structural_tokens(s, expected):
    assert tokenize(s) == expected


# --- null ---------------------------------------------------------------------

@pytest.mark.parametrize("s", ["null", " null", "null ", " null "])
def test_null(s):
    assert tokenize(s) == [NULL]


@pytest.mark.parametrize("bad", ["nul", "NULL", "Null", "none"])
def test_null_invalid(bad):
    with pytest.raises(ParsingError):
        tokenize(bad)


# --- booleans -----------------------------------------------------------------

@pytest.mark.parametrize("s,expected", [
    ("true", [BOOL(True)]),
    ("false", [BOOL(False)]),
    (" true ", [BOOL(True)]),
    (" false ", [BOOL(False)]),
])
def test_bool(s, expected):
    assert tokenize(s) == expected


@pytest.mark.parametrize("bad", ["True", "False", "tru", "fals", "truex", "falsex"])
def test_bool_invalid(bad):
    with pytest.raises(ParsingError):
        tokenize(bad)


# --- numbers ------------------------------------------------------------------

@pytest.mark.parametrize("s,expected", [
    ("0", [NUM(0)]),
    ("42", [NUM(42)]),
    ("-1", [NUM(-1)]),
    ("3.14", [NUM(3.14)]),
    ("1e5", [NUM(1e5)]),
    ("1.5e-3", [NUM(1.5e-3)]),
    ("-0.5", [NUM(-0.5)]),
    (" 99 ", [NUM(99)]),
])
def test_number(s, expected):
    assert tokenize(s) == expected


@pytest.mark.parametrize("bad", [".5", "-", "1.", "1e", "+1"])
def test_number_invalid(bad):
    with pytest.raises(ParsingError):
        tokenize(bad)


# --- strings ------------------------------------------------------------------

@pytest.mark.parametrize("s,expected", [
    ('"hello"', [STR("hello")]),
    ('""', [STR("")]),
    ('" "', [STR(" ")]),
    ('"日本語"', [STR("日本語")]),
    ('"with : colon , comma"', [STR("with : colon , comma")]),
])
def test_string(s, expected):
    assert tokenize(s) == expected


@pytest.mark.parametrize("bad", ['"hello', '"', 'hello"', "hello"])
def test_string_invalid(bad):
    with pytest.raises(ParsingError):
        tokenize(bad)


# --- unknown character --------------------------------------------------------

@pytest.mark.parametrize("bad", ["!", "@", "abc", ";"])
def test_unknown_character(bad):
    with pytest.raises(ParsingError):
        tokenize(bad)


# --- compound expressions -----------------------------------------------------

def test_simple_object():
    tokens = tokenize('{"name": "Alice", "age": 30}')
    assert tokens == [
        LB,
        STR("name"), COLON, STR("Alice"),
        COMMA,
        STR("age"), COLON, NUM(30),
        RB,
    ]


def test_simple_array():
    tokens = tokenize('[1, "two", null, true, false]')
    assert tokens == [
        LBK,
        NUM(1), COMMA,
        STR("two"), COMMA,
        NULL, COMMA,
        BOOL(True), COMMA,
        BOOL(False),
        RBK,
    ]


def test_nested_object():
    tokens = tokenize('{"a": {"b": 1}}')
    assert tokens == [
        LB,
        STR("a"), COLON,
        LB, STR("b"), COLON, NUM(1), RB,
        RB,
    ]


def test_nested_array():
    tokens = tokenize("[[1, 2], [3]]")
    assert tokens == [
        LBK,
        LBK, NUM(1), COMMA, NUM(2), RBK,
        COMMA,
        LBK, NUM(3), RBK,
        RBK,
    ]


def test_empty_containers():
    assert tokenize("{}") == [LB, RB]
    assert tokenize("[]") == [LBK, RBK]


def test_whitespace_ignored():
    assert tokenize(' { "k" : 1 } ') == [LB, STR("k"), COLON, NUM(1), RB]


def test_all_primitives_in_array():
    tokens = tokenize('[null, true, false, 0, 1.5, "x"]')
    assert tokens == [
        LBK,
        NULL, COMMA,
        BOOL(True), COMMA,
        BOOL(False), COMMA,
        NUM(0), COMMA,
        NUM(1.5), COMMA,
        STR("x"),
        RBK,
    ]


def test_multiline_json():
    s = '{\n  "name": "Alice",\n  "age": 30\n}'
    tokens = tokenize(s)
    assert tokens == [LB, STR("name"), COLON, STR("Alice"), COMMA, STR("age"), COLON, NUM(30), RB]


def test_multiple_values_tokenized():
    # tokenize doesn't enforce a single top-level value — that's the parser's job
    tokens = tokenize("1 2 3")
    assert tokens == [NUM(1), NUM(2), NUM(3)]


def test_consecutive_structural_tokens():
    tokens = tokenize("{}{}")
    assert tokens == [LB, RB, LB, RB]
