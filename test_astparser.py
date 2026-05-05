import pytest

from astparser import (
    ArrayNode,
    BoolNode,
    MemberNode,
    NullNode,
    NumberNode,
    ObjectNode,
    ParsingError,
    StringNode,
    Token,
    TokenType,
    evaluate,
    parse,
    parsestr,
)


# --- token builders -----------------------------------------------------------

def T(type, value=None):
    return Token(type, value)


LB = T(TokenType.LBRACE)
RB = T(TokenType.RBRACE)
LBK = T(TokenType.LBRACKET)
RBK = T(TokenType.RBRACKET)
COLON = T(TokenType.COLON)
COMMA = T(TokenType.COMMA)
NULL = T(TokenType.NULL, None)


def STR(v):
    return T(TokenType.STRING, v)


def NUM(v):
    return T(TokenType.NUMBER, v)


def BOOL(v):
    return T(TokenType.BOOL, v)


# --- primitives ---------------------------------------------------------------

def test_null():
    assert parse([NULL]) == NullNode()


@pytest.mark.parametrize("value", [True, False])
def test_bool(value):
    assert parse([BOOL(value)]) == BoolNode(value)


@pytest.mark.parametrize("value", [0, 42, -1, 3.14, 1e5])
def test_number(value):
    assert parse([NUM(value)]) == NumberNode(value)


@pytest.mark.parametrize("value", ["hello", "", " ", "日本語"])
def test_string(value):
    assert parse([STR(value)]) == StringNode(value)


# --- objects ------------------------------------------------------------------

def test_empty_object():
    assert parse([LB, RB]) == ObjectNode([])


def test_object_single_member():
    tokens = [LB, STR("k"), COLON, NUM(1), RB]
    assert parse(tokens) == ObjectNode([MemberNode(StringNode("k"), NumberNode(1))])


def test_object_multiple_members():
    tokens = [
        LB,
        STR("a"), COLON, NUM(1), COMMA,
        STR("b"), COLON, BOOL(True), COMMA,
        STR("c"), COLON, NULL,
        RB,
    ]
    assert parse(tokens) == ObjectNode([
        MemberNode(StringNode("a"), NumberNode(1)),
        MemberNode(StringNode("b"), BoolNode(True)),
        MemberNode(StringNode("c"), NullNode()),
    ])


def test_object_member_ordering_preserved():
    tokens = [
        LB,
        STR("z"), COLON, NUM(1), COMMA,
        STR("a"), COLON, NUM(2),
        RB,
    ]
    result = parse(tokens)
    assert [m.key.value for m in result.members] == ["z", "a"]


@pytest.mark.parametrize("tokens", [
    [LB],                                       # unclosed
    [RB],                                       # stray close
    [LB, STR("k"), RB],                         # missing colon and value
    [LB, STR("k"), COLON, RB],                  # missing value
    [LB, STR("k"), COLON, NUM(1)],              # unclosed after value
    [LB, STR("k"), COLON, NUM(1), COMMA, RB],   # trailing comma
    [LB, COMMA, STR("k"), COLON, NUM(1), RB],   # leading comma
    [LB, NUM(1), COLON, NUM(1), RB],            # non-string key
    [LB, STR("k"), NUM(1), RB],                 # missing colon
    [LB, STR("a"), COLON, NUM(1), STR("b"), COLON, NUM(2), RB],  # missing comma
])
def test_invalid_object(tokens):
    with pytest.raises(ParsingError):
        parse(tokens)


# --- arrays -------------------------------------------------------------------

def test_empty_array():
    assert parse([LBK, RBK]) == ArrayNode([])


def test_array_single_element():
    assert parse([LBK, NUM(1), RBK]) == ArrayNode([NumberNode(1)])


def test_array_multiple_elements():
    tokens = [LBK, NUM(1), COMMA, STR("x"), COMMA, NULL, COMMA, BOOL(False), RBK]
    assert parse(tokens) == ArrayNode([
        NumberNode(1),
        StringNode("x"),
        NullNode(),
        BoolNode(False),
    ])


def test_array_element_ordering_preserved():
    tokens = [LBK, NUM(3), COMMA, NUM(1), COMMA, NUM(2), RBK]
    result = parse(tokens)
    assert [e.value for e in result.elements] == [3, 1, 2]


@pytest.mark.parametrize("tokens", [
    [LBK],                                  # unclosed
    [RBK],                                  # stray close
    [LBK, NUM(1)],                          # unclosed after value
    [LBK, COMMA, RBK],                      # bare comma
    [LBK, NUM(1), COMMA, RBK],              # trailing comma
    [LBK, COMMA, NUM(1), RBK],              # leading comma
    [LBK, NUM(1), NUM(2), RBK],             # missing comma
    [LBK, NUM(1), COMMA, COMMA, NUM(2), RBK],  # double comma
])
def test_invalid_array(tokens):
    with pytest.raises(ParsingError):
        parse(tokens)


# --- nesting ------------------------------------------------------------------

def test_object_in_object():
    tokens = [LB, STR("a"), COLON, LB, STR("b"), COLON, NUM(1), RB, RB]
    assert parse(tokens) == ObjectNode([
        MemberNode(
            StringNode("a"),
            ObjectNode([MemberNode(StringNode("b"), NumberNode(1))]),
        ),
    ])


def test_array_in_array():
    tokens = [LBK, LBK, NUM(1), RBK, COMMA, LBK, NUM(2), RBK, RBK]
    assert parse(tokens) == ArrayNode([
        ArrayNode([NumberNode(1)]),
        ArrayNode([NumberNode(2)]),
    ])


def test_array_of_objects():
    tokens = [
        LBK,
        LB, STR("k"), COLON, NUM(1), RB,
        COMMA,
        LB, STR("k"), COLON, NUM(2), RB,
        RBK,
    ]
    assert parse(tokens) == ArrayNode([
        ObjectNode([MemberNode(StringNode("k"), NumberNode(1))]),
        ObjectNode([MemberNode(StringNode("k"), NumberNode(2))]),
    ])


def test_object_with_array_value():
    tokens = [LB, STR("xs"), COLON, LBK, NUM(1), COMMA, NUM(2), RBK, RB]
    assert parse(tokens) == ObjectNode([
        MemberNode(
            StringNode("xs"),
            ArrayNode([NumberNode(1), NumberNode(2)]),
        ),
    ])


# --- top-level constraints ----------------------------------------------------

def test_empty_token_stream_raises():
    with pytest.raises(ParsingError):
        parse([])


def test_trailing_tokens_raise():
    with pytest.raises(ParsingError):
        parse([NUM(1), NUM(2)])


def test_trailing_tokens_after_object_raise():
    with pytest.raises(ParsingError):
        parse([LB, RB, LB, RB])


@pytest.mark.parametrize("stray", [COMMA, COLON, RB, RBK])
def test_stray_structural_token_raises(stray):
    with pytest.raises(ParsingError):
        parse([stray])


# --- end-to-end (parsestr) ----------------------------------------------------
# parsestr drives the full pipeline (tokenize → parse → evaluate) and matches
# parser.py's signature, so we exercise it on whole JSON literals.

@pytest.mark.parametrize("source,expected", [
    ("null", None),
    ("true", True),
    ("false", False),
    ("0", 0),
    ("-1.5", -1.5),
    ('"hi"', "hi"),
    ("[]", []),
    ("{}", {}),
    ("[1, 2, 3]", [1, 2, 3]),
    ('{"a": 1}', {"a": 1}),
    ('{"a": 1, "b": [true, null, "x"]}', {"a": 1, "b": [True, None, "x"]}),
    ('[{"k": [1, 2]}, {"k": []}]', [{"k": [1, 2]}, {"k": []}]),
    ('{"a": {"b": {"c": 1}}}', {"a": {"b": {"c": 1}}}),
])
def test_parsestr(source, expected):
    assert parsestr(source) == expected


def test_evaluate_unknown_node_raises():
    class FakeNode:
        pass
    with pytest.raises(ParsingError):
        evaluate(FakeNode())
