from dataclasses import dataclass
from enum import Enum, auto

from parser import DIGITS, ParsingError, parse_bool, parse_null, parse_number, parse_string, skip_ws


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
            value, pos = parse_null(s, pos)
            tokens.append(Token(TokenType.NULL, value))
        elif c in "tf":
            value, pos = parse_bool(s, pos)
            tokens.append(Token(TokenType.BOOL, value))
        elif c == "-" or c in DIGITS:
            value, pos = parse_number(s, pos)
            tokens.append(Token(TokenType.NUMBER, value))
        elif c == '"':
            value, pos = parse_string(s, pos)
            tokens.append(Token(TokenType.STRING, value))
        else:
            raise ParsingError(f"unexpected character {c!r} at position {pos}")
    return tokens
