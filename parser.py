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
    
    fixed_parsing_dict = {
        "null": None,
        "true": True,
        "false": False,
    }
    target_primitive = None
    if first_char == "n":
        target_primitive = "null"
    if first_char == "t":
        target_primitive = "true"
    if first_char == "f":
        target_primitive = "false"

    if target_primitive: 
        possible_primitive = []
        for index in range(first_char_index, min(first_char_index+len(target_primitive), len(json_str))):
            possible_primitive.append(json_str[index])
        if "".join(possible_primitive) == target_primitive:
            return fixed_parsing_dict[target_primitive]
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
