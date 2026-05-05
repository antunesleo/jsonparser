class ParsingError(Exception):
    pass


WHITESPACE = " \t\n\r"
DIGITS = "0123456789"


def skip_ws(s, pos):
    while pos < len(s) and s[pos] in WHITESPACE:
        pos += 1
    return pos


def parse_null(s, pos):
    if not s.startswith("null", pos):
        raise ParsingError("aha!")
    return None, pos + 4


def parse_bool(s, pos):
    if s.startswith("true", pos):
        return True, pos + 4
    if s.startswith("false", pos):
        return False, pos + 5
    raise ParsingError("aha!")


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
    raise ParsingError("aha!")


def parsestr(json_str: str):
    value, pos = parse_value(json_str, 0)
    pos = skip_ws(json_str, pos)
    if pos != len(json_str):
        raise ParsingError("aha!")
    return value
