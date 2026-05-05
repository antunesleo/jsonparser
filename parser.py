# Single-phase scannerless recursive descent parser for JSON.
#
# ── BACKGROUND: THE TWO PHASES OF PARSING ────────────────────────────────────
#
# Parsing is traditionally split into two phases:
#
#   1. Lexical analysis (lexing / tokenizing)
#      Scans raw characters and groups them into tokens — the smallest meaningful
#      chunks of the language. Each token has a type and a value, for example:
#
#        Input:  { "name" : "Alice" , "age" : 30 }
#        Tokens: LBRACE  STRING("name")  COLON  STRING("Alice")  COMMA
#                STRING("age")  COLON  NUMBER(30)  RBRACE
#
#      The token stream is flat (a sequence, not a tree) and raw (it preserves
#      everything: source positions, comments, whitespace — things the parser
#      does not care about but other tools like formatters or debuggers do).
#
#   2. Syntactic analysis (parsing)
#      Consumes the token stream and enforces the grammar, producing an
#      AST (Abstract Syntax Tree) — a hierarchical structure that captures
#      relationships between tokens:
#
#        ObjectNode
#          KeyValueNode(StringNode("name"), StringNode("Alice"))
#          KeyValueNode(StringNode("age"),  NumberNode(30))
#
#      Notice that structural tokens like LBRACE, RBRACE, COLON, COMMA are gone —
#      their job was to delimit structure, which is now encoded in the tree itself.
#
#      AST nodes are built from the *values* extracted from tokens, not from the
#      token objects themselves (though some parsers do store the original token
#      in each node to preserve position info for error messages).
#
# ── TOKEN STREAM vs AST ───────────────────────────────────────────────────────
#
#   Token stream: flat, complete, preserves source positions and comments.
#   AST:          hierarchical, lossy (drops punctuation and metadata), captures meaning.
#
#   The main reason to keep them as separate phases is reuse and separation of concerns:
#   different tools need different things from the same input. A syntax highlighter only
#   needs tokens; a compiler needs the AST; a formatter needs both (AST for structure,
#   token stream to recover the original comments and whitespace). With a clean separation
#   each tool reuses the same lexer without re-implementing it.
#
#   A secondary benefit is error reporting: if parsing fails, the token stream still holds
#   exact source positions, enabling "unexpected token X at line 3, col 7" messages.
#
# ── WHAT THIS IMPLEMENTATION DOES INSTEAD ────────────────────────────────────
#
#   Both phases are merged into a single pass directly over the characters.
#   No token objects are created, no AST is built — the final Python value is
#   constructed directly as the input is consumed.
#
#   This is valid for JSON because one character of lookahead is always enough
#   to decide which token type follows — no backtracking, no ambiguity.
#
#   Memory comparison:
#     Two-phase: O(n) token stream + O(n) AST + O(depth) call stack + output value
#     This impl: O(depth) call stack + output value
#
#   The trade-off: an AST is worth the memory cost when multiple passes are needed
#   (a compiler does type checking, optimization, and code generation — all on the
#   same tree). For JSON there is only ever one pass, so the intermediate structures
#   buy nothing.


class ParsingError(Exception):
    pass


WHITESPACE = " \t\n\r"
DIGITS = "0123456789"


# --- Lexical analysis ----------------------------------------------------------
# The functions below do the work a separate lexer would do: scan raw characters,
# recognize a token boundary, and return the token's value. In a two-phase design
# these would return a Token object (type + raw text + position) instead of the
# final Python value, leaving interpretation to the parser phase.

# Pure lexer concern: a real lexer silently absorbs whitespace between tokens so
# the parser never sees it. We call this explicitly wherever whitespace is allowed.
def skip_ws(s, pos):
    while pos < len(s) and s[pos] in WHITESPACE:
        pos += 1
    return pos


# Recognizes a NULL keyword token.
def parse_null(s, pos):
    if not s.startswith("null", pos):
        raise ParsingError("aha!")
    return None, pos + 4


# Recognizes a BOOL keyword token (true / false).
def parse_bool(s, pos):
    if s.startswith("true", pos):
        return True, pos + 4
    if s.startswith("false", pos):
        return False, pos + 5
    raise ParsingError("aha!")


# Recognizes a NUMBER token. Scans the full lexeme (sign, integer part, optional
# decimal and exponent) before converting — matching what a lexer's regex would capture.
def parse_number(s, pos):
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


# Recognizes a STRING token, returning the content between the quotes.
def parse_string(s, pos):
    if pos >= len(s) or s[pos] != '"':
        raise ParsingError("aha!")
    pos += 1
    start = pos
    while pos < len(s) and s[pos] != '"':
        pos += 1
    if pos >= len(s):
        raise ParsingError("aha!")
    return s[start:pos], pos + 1


# --- Syntactic analysis -------------------------------------------------------
# The functions below enforce the JSON grammar. In a two-phase design this code
# would consume a token stream rather than raw characters, calling next_token()
# instead of parse_string() / skip_ws() directly.
#
# Grammar rules (EBNF):
#   object → '{' (string ':' value (',' string ':' value)*)? '}'
#   array  → '[' (value (',' value)*)? ']'
#   value  → null | bool | number | string | object | array


def parse_object(s, pos):
    if pos >= len(s) or s[pos] != "{":
        raise ParsingError("ha!")
    pos += 1
    pos = skip_ws(s, pos)

    if pos < len(s) and s[pos] == "}":
        return {}, pos + 1

    result = {}
    while True:
        pos = skip_ws(s, pos)
        key, pos = parse_string(s, pos)

        pos = skip_ws(s, pos)
        if pos >= len(s) or s[pos] != ":":
            raise ParsingError("ha!")
        pos += 1

        value, pos = parse_value(s, pos)
        result[key] = value

        pos = skip_ws(s, pos)
        if pos >= len(s):
            raise ParsingError("ha!")
        if s[pos] == "}":
            return result, pos + 1
        if s[pos] != ",":
            raise ParsingError("ha!")
        pos += 1


def parse_list(s, pos):
    if pos >= len(s) or s[pos] != "[":
        raise ParsingError("ha!")
    pos += 1
    pos = skip_ws(s, pos)

    if pos < len(s) and s[pos] == "]":
        return [], pos + 1

    result = []
    while True:
        value, pos = parse_value(s, pos)
        result.append(value)

        pos = skip_ws(s, pos)
        if pos >= len(s):
            raise ParsingError("ha!")
        if s[pos] == "]":
            return result, pos + 1
        if s[pos] != ",":
            raise ParsingError("ha!")
        pos += 1


# Token-type detection: peeking at the first character is always sufficient to
# decide which token (and therefore which grammar branch) follows. This is the
# equivalent of a lexer's dispatch table.
def parse_value(s, pos):
    pos = skip_ws(s, pos)
    if pos >= len(s):
        raise ParsingError("aha!")
    c = s[pos]
    if c == "n":
        return parse_null(s, pos)
    if c == "t" or c == "f":
        return parse_bool(s, pos)
    if c == "-" or c in DIGITS:
        return parse_number(s, pos)
    if c == '"':
        return parse_string(s, pos)
    if c == "{":
        return parse_object(s, pos)
    if c == "[":
        return parse_list(s, pos)
    raise ParsingError("aha!")


def parsestr(json_str: str):
    value, pos = parse_value(json_str, 0)
    pos = skip_ws(json_str, pos)
    if pos != len(json_str):
        raise ParsingError("aha!")
    return value
