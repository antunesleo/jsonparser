# Two-phase JSON pipeline: lexer + parser + evaluator, all in one module.
#
#   tokenize(s)          str        -> list[Token]
#   parse(tokens)        list[Token] -> Node (AST)
#   evaluate(node)       Node       -> Python value
#
# The phases are kept distinct in code even though they live in the same file:
# tokens know nothing about the AST, the AST knows nothing about evaluation.
# A pretty-printer or schema validator could be added later as another walk
# without touching the parser or the lexer.

from dataclasses import dataclass
from enum import Enum, auto


class ParsingError(Exception):
    pass


WHITESPACE = " \t\n\r"
DIGITS = "0123456789"


# --- Lexer --------------------------------------------------------------------
# Scans raw characters into a flat list of tokens. Each helper recognizes one
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


@dataclass
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


def tokenize(s: str) -> list[Token]:
    tokens = []
    pos = 0
    while True:
        pos = skip_ws(s, pos)
        if pos >= len(s):
            break
        c = s[pos]
        if c == "{":
            tokens.append(Token(TokenType.LBRACE))
            pos += 1
        elif c == "}":
            tokens.append(Token(TokenType.RBRACE))
            pos += 1
        elif c == "[":
            tokens.append(Token(TokenType.LBRACKET))
            pos += 1
        elif c == "]":
            tokens.append(Token(TokenType.RBRACKET))
            pos += 1
        elif c == ":":
            tokens.append(Token(TokenType.COLON))
            pos += 1
        elif c == ",":
            tokens.append(Token(TokenType.COMMA))
            pos += 1
        elif c == "n":
            value, pos = lex_null(s, pos)
            tokens.append(Token(TokenType.NULL, value))
        elif c in "tf":
            value, pos = lex_bool(s, pos)
            tokens.append(Token(TokenType.BOOL, value))
        elif c == "-" or c in DIGITS:
            value, pos = lex_number(s, pos)
            tokens.append(Token(TokenType.NUMBER, value))
        elif c == '"':
            value, pos = lex_string(s, pos)
            tokens.append(Token(TokenType.STRING, value))
        else:
            raise ParsingError(f"unexpected character {c!r} at position {pos}")
    return tokens


# --- AST node definitions -----------------------------------------------------
# Nodes carry data only and have no behavior. Each class corresponds to one
# grammar production; fields name the grammatical positions (e.g. MemberNode
# has key/value, not generic children) so the tree mirrors the grammar.


class Node:
    pass


@dataclass
class NullNode(Node):
    pass


@dataclass
class BoolNode(Node):
    value: bool


@dataclass
class NumberNode(Node):
    value: int | float


@dataclass
class StringNode(Node):
    value: str


@dataclass
class MemberNode(Node):
    key: StringNode
    value: Node


@dataclass
class ObjectNode(Node):
    members: list[MemberNode]


@dataclass
class ArrayNode(Node):
    elements: list[Node]


# --- Token-stream parser ------------------------------------------------------
# Each function returns (node, new_pos), threading pos through the recursion
# the same way parser.py threads a character index.
#
# Grammar (EBNF):
#   value  → NULL | BOOL | NUMBER | STRING | object | array
#   object → LBRACE (member (COMMA member)*)? RBRACE
#   member → STRING COLON value
#   array  → LBRACKET (value (COMMA value)*)? RBRACKET


def parse_value(tokens: list[Token], pos: int) -> tuple[Node, int]:
    if pos >= len(tokens):
        raise ParsingError("unexpected end of tokens")
    tok = tokens[pos]
    if tok.type == TokenType.NULL:
        return NullNode(), pos + 1
    if tok.type == TokenType.BOOL:
        return BoolNode(tok.value), pos + 1
    if tok.type == TokenType.NUMBER:
        return NumberNode(tok.value), pos + 1
    if tok.type == TokenType.STRING:
        return StringNode(tok.value), pos + 1
    if tok.type == TokenType.LBRACE:
        return parse_object(tokens, pos)
    if tok.type == TokenType.LBRACKET:
        return parse_array(tokens, pos)
    raise ParsingError(f"unexpected token {tok.type.name}")


def parse_object(tokens: list[Token], pos: int) -> tuple[ObjectNode, int]:
    if pos >= len(tokens) or tokens[pos].type != TokenType.LBRACE:
        raise ParsingError("expected '{'")
    pos += 1

    if pos < len(tokens) and tokens[pos].type == TokenType.RBRACE:
        return ObjectNode([]), pos + 1

    members: list[MemberNode] = []
    while True:
        if pos >= len(tokens) or tokens[pos].type != TokenType.STRING:
            raise ParsingError("expected string key")
        key = StringNode(tokens[pos].value)
        pos += 1

        if pos >= len(tokens) or tokens[pos].type != TokenType.COLON:
            raise ParsingError("expected ':'")
        pos += 1

        value, pos = parse_value(tokens, pos)
        members.append(MemberNode(key, value))

        if pos >= len(tokens):
            raise ParsingError("unexpected end of tokens")
        if tokens[pos].type == TokenType.RBRACE:
            return ObjectNode(members), pos + 1
        if tokens[pos].type != TokenType.COMMA:
            raise ParsingError("expected ',' or '}'")
        pos += 1


def parse_array(tokens: list[Token], pos: int) -> tuple[ArrayNode, int]:
    if pos >= len(tokens) or tokens[pos].type != TokenType.LBRACKET:
        raise ParsingError("expected '['")
    pos += 1

    if pos < len(tokens) and tokens[pos].type == TokenType.RBRACKET:
        return ArrayNode([]), pos + 1

    elements: list[Node] = []
    while True:
        value, pos = parse_value(tokens, pos)
        elements.append(value)

        if pos >= len(tokens):
            raise ParsingError("unexpected end of tokens")
        if tokens[pos].type == TokenType.RBRACKET:
            return ArrayNode(elements), pos + 1
        if tokens[pos].type != TokenType.COMMA:
            raise ParsingError("expected ',' or ']'")
        pos += 1


def parse(tokens: list[Token]) -> Node:
    node, pos = parse_value(tokens, 0)
    if pos != len(tokens):
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
