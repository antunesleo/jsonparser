class ParsingError(Exception):
    pass


def parsestr(json_str: str):
    stack = []

    for char in json_str:
        if char == " ":
            continue
        if char == "{":
            if len(stack) > 0:
                raise ParsingError("ha!")
            
            stack.append(char)
        
        if char == "}":
            if not stack:
                raise ParsingError("ha!")
        
            stack.pop()
        
    if stack:
        raise ParsingError("ha!")
    
    return {}
