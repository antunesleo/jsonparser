# Two-phase JSON pipeline: lexer + parser + evaluator, all in one module.
#
#   tokenize(s)          str             -> Iterator[Token]
#   parse(tokens)        Iterable[Token] -> Node (AST)
#   evaluate(node)       Node            -> Python value
#
# The phases are kept distinct in code even though they live in the same file:
# tokens know nothing about the AST, the AST knows nothing about evaluation.
# A pretty-printer or schema validator could be added later as another walk
# without touching the parser or the lexer.

from dataclasses import dataclass
from enum import Enum, auto
from typing import Iterable, Iterator


class ParsingError(Exception):
    pass


WHITESPACE = " \t\n\r"
DIGITS = "0123456789"


# --- Lexer --------------------------------------------------------------------
# Scans raw characters into a stream of tokens. Each helper recognizes one
# token kind; tokenize() dispatches on the first character of each token, since
# one-char lookahead is always enough to decide which JSON token follows.


class TokenType(Enum):
    LBRACE = auto()
    RBRACE = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    COLON = auto()
    COMMA = auto()
    STRING = auto()
    NUMBER = auto()
    BOOL = auto()
    NULL = auto()


@dataclass(slots=True)
class Token:
    type: TokenType
    value: object = None


def skip_ws(s, pos):
    while pos < len(s) and s[pos] in WHITESPACE:
        pos += 1
    return pos


def lex_null(s, pos):
    if not s.startswith("null", pos):
        raise ParsingError("aha!")
    return None, pos + 4


def lex_bool(s, pos):
    if s.startswith("true", pos):
        return True, pos + 4
    if s.startswith("false", pos):
        return False, pos + 5
    raise ParsingError("aha!")


# Scans the full numeric lexeme (sign, integer part, optional decimal and
# exponent) before converting — matches what a regex-based lexer would capture.
def lex_number(s, pos):
    start = pos

    if pos < len(s) and s[pos] == "-":
        pos += 1

    if pos >= len(s) or s[pos] not in DIGITS:
        raise ParsingError("aha!")
    if s[pos] == "0":
        pos += 1
    else:
        while pos < len(s) and s[pos] in DIGITS:
            pos += 1

    is_float = False

    if pos < len(s) and s[pos] == ".":
        is_float = True
        pos += 1
        if pos >= len(s) or s[pos] not in DIGITS:
            raise ParsingError("aha!")
        while pos < len(s) and s[pos] in DIGITS:
            pos += 1

    if pos < len(s) and s[pos] in "eE":
        is_float = True
        pos += 1
        if pos < len(s) and s[pos] in "+-":
            pos += 1
        if pos >= len(s) or s[pos] not in DIGITS:
            raise ParsingError("aha!")
        while pos < len(s) and s[pos] in DIGITS:
            pos += 1

    text = s[start:pos]
    return (float(text) if is_float else int(text)), pos


def lex_string(s, pos):
    if pos >= len(s) or s[pos] != '"':
        raise ParsingError("aha!")
    pos += 1
    start = pos
    while pos < len(s) and s[pos] != '"':
        pos += 1
    if pos >= len(s):
        raise ParsingError("aha!")
    return s[start:pos], pos + 1


def tokenize(s: str) -> Iterator[Token]:
    pos = 0
    while True:
        pos = skip_ws(s, pos)
        if pos >= len(s):
            return
        c = s[pos]
        if c == "{":
            yield Token(TokenType.LBRACE)
            pos += 1
        elif c == "}":
            yield Token(TokenType.RBRACE)
            pos += 1
        elif c == "[":
            yield Token(TokenType.LBRACKET)
            pos += 1
        elif c == "]":
            yield Token(TokenType.RBRACKET)
            pos += 1
        elif c == ":":
            yield Token(TokenType.COLON)
            pos += 1
        elif c == ",":
            yield Token(TokenType.COMMA)
            pos += 1
        elif c == "n":
            value, pos = lex_null(s, pos)
            yield Token(TokenType.NULL, value)
        elif c in "tf":
            value, pos = lex_bool(s, pos)
            yield Token(TokenType.BOOL, value)
        elif c == "-" or c in DIGITS:
            value, pos = lex_number(s, pos)
            yield Token(TokenType.NUMBER, value)
        elif c == '"':
            value, pos = lex_string(s, pos)
            yield Token(TokenType.STRING, value)
        else:
            raise ParsingError(f"unexpected character {c!r} at position {pos}")


# --- AST node definitions -----------------------------------------------------
# Nodes carry data only and have no behavior. Each class corresponds to one
# grammar production; fields name the grammatical positions (e.g. MemberNode
# has key/value, not generic children) so the tree mirrors the grammar.


class Node:
    __slots__ = ()


@dataclass(slots=True)
class NullNode(Node):
    pass


@dataclass(slots=True)
class BoolNode(Node):
    value: bool


@dataclass(slots=True)
class NumberNode(Node):
    value: int | float


@dataclass(slots=True)
class StringNode(Node):
    value: str


@dataclass(slots=True)
class MemberNode(Node):
    key: StringNode
    value: Node


@dataclass(slots=True)
class ObjectNode(Node):
    members: list[MemberNode]


@dataclass(slots=True)
class ArrayNode(Node):
    elements: list[Node]


# --- Token-stream parser ------------------------------------------------------
# Each function pulls tokens from a single-token-lookahead stream so the full
# token list never has to be materialized — tokenize() can stream straight in.
#
# Grammar (EBNF):
#   value  → NULL | BOOL | NUMBER | STRING | object | array
#   object → LBRACE (member (COMMA member)*)? RBRACE
#   member → STRING COLON value
#   array  → LBRACKET (value (COMMA value)*)? RBRACKET


# Sentinel for "no token cached yet" — distinct from None, which is what peek()
# returns at end of stream.
_UNFETCHED = object()


class TokenStream:
    __slots__ = ("_it", "_current")

    def __init__(self, it: Iterable[Token]):
        self._it = iter(it)
        self._current = _UNFETCHED

    def peek(self) -> Token | None:
        if self._current is _UNFETCHED:
            self._current = next(self._it, None)
        return self._current

    def next_one(self) -> Token | None:
        token = self.peek()
        self._current = _UNFETCHED
        return token


def parse_value(token_stream: TokenStream) -> Node:
    token = token_stream.peek()
    if token is None:
        raise ParsingError("unexpected end of tokens")
    if token.type == TokenType.NULL:
        token_stream.next_one()
        return NullNode()
    if token.type == TokenType.BOOL:
        token_stream.next_one()
        return BoolNode(token.value)
    if token.type == TokenType.NUMBER:
        token_stream.next_one()
        return NumberNode(token.value)
    if token.type == TokenType.STRING:
        token_stream.next_one()
        return StringNode(token.value)
    if token.type == TokenType.LBRACE:
        return parse_object(token_stream)
    if token.type == TokenType.LBRACKET:
        return parse_array(token_stream)
    raise ParsingError(f"unexpected token {token.type.name}")


def parse_object(token_stream: TokenStream) -> ObjectNode:
    token = token_stream.peek()
    if token is None or token.type != TokenType.LBRACE:
        raise ParsingError("expected '{'")
    token_stream.next_one()

    token = token_stream.peek()
    if token is not None and token.type == TokenType.RBRACE:
        token_stream.next_one()
        return ObjectNode([])

    members: list[MemberNode] = []
    while True:
        token = token_stream.peek()
        if token is None or token.type != TokenType.STRING:
            raise ParsingError("expected string key")
        key = StringNode(token.value)
        token_stream.next_one()

        token = token_stream.peek()
        if token is None or token.type != TokenType.COLON:
            raise ParsingError("expected ':'")
        token_stream.next_one()

        value = parse_value(token_stream)
        members.append(MemberNode(key, value))

        token = token_stream.peek()
        if token is None:
            raise ParsingError("unexpected end of tokens")
        if token.type == TokenType.RBRACE:
            token_stream.next_one()
            return ObjectNode(members)
        if token.type != TokenType.COMMA:
            raise ParsingError("expected ',' or '}'")
        token_stream.next_one()


def parse_array(token_stream: TokenStream) -> ArrayNode:
    token = token_stream.peek()
    if token is None or token.type != TokenType.LBRACKET:
        raise ParsingError("expected '['")
    token_stream.next_one()

    token = token_stream.peek()
    if token is not None and token.type == TokenType.RBRACKET:
        token_stream.next_one()
        return ArrayNode([])

    elements: list[Node] = []
    while True:
        value = parse_value(token_stream)
        elements.append(value)

        token = token_stream.peek()
        if token is None:
            raise ParsingError("unexpected end of tokens")
        if token.type == TokenType.RBRACKET:
            token_stream.next_one()
            return ArrayNode(elements)
        if token.type != TokenType.COMMA:
            raise ParsingError("expected ',' or ']'")
        token_stream.next_one()


def parse(tokens: Iterable[Token]) -> Node:
    token_stream = TokenStream(tokens)
    node = parse_value(token_stream)
    if token_stream.peek() is not None:
        raise ParsingError("trailing tokens")
    return node


# --- Evaluator ----------------------------------------------------------------
# Walks the AST and produces the equivalent native Python value. One match
# arm per node kind, recursing into children for the composite ones.


def evaluate(node: Node):
    if isinstance(node, NullNode):
        return None
    if isinstance(node, (BoolNode, NumberNode, StringNode)):
        return node.value
    if isinstance(node, ArrayNode):
        return [evaluate(e) for e in node.elements]
    if isinstance(node, ObjectNode):
        return {m.key.value: evaluate(m.value) for m in node.members}
    raise ParsingError(f"unknown node {type(node).__name__}")


# Drop-in equivalent of parser.py's parsestr: drives the full pipeline so callers
# get a Python value without having to compose the three phases themselves.
def parsestr(json_str: str):
    return evaluate(parse(tokenize(json_str)))
