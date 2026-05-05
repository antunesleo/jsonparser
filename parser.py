class ParsingError(Exception):
    pass


def parsestr(json_str: str):
    stack = []

    first_char_index = 0
    for index, char in enumerate(json_str):
        if char != " ":
            first_char_index = index
            break

    first_char = json_str[first_char_index]
    if first_char == "n":
        possible_null = []
        for index in range(first_char_index, min(first_char_index+4, len(json_str))):
            possible_null.append(json_str[index])
        if "".join(possible_null) == "null":
            return None
        raise ParsingError("aha!")

    if first_char == "{":
        for index in range(first_char_index, len(json_str)):
            char = json_str[index]

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
    
    raise ParsingError("ha!")
