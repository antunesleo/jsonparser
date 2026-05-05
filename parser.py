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
    target_fixed_primitive = None
    if first_char == "n":
        target_fixed_primitive = "null"
    if first_char == "t":
        target_fixed_primitive = "true"
    if first_char == "f":
        target_fixed_primitive = "false"

    if target_fixed_primitive: 
        possible_primitive = []
        for index in range(first_char_index, min(first_char_index+len(target_fixed_primitive), len(json_str))):
            possible_primitive.append(json_str[index])
        if "".join(possible_primitive) == target_fixed_primitive:
            return fixed_parsing_dict[target_fixed_primitive]
        raise ParsingError("aha!")

    zero_to_9 = ("0", "1", "2", "3", "4", "5", "6", "7", "8", "9")
    starting_number_chars = ("-",) + zero_to_9
    number_chars = zero_to_9 + (".", "e")
    if first_char in starting_number_chars:
        is_float = False
        is_exp = False
        possible_number = []
        for index in range(first_char_index, len(json_str)):
            possible_char = json_str[index]
            if possible_char not in number_chars:
                break
            if possible_char in ".":
                if is_float:
                    raise ParsingError("aha!")
                is_float = True
            if possible_char in "e":
                if is_exp:
                    raise ParsingError("aha!")
                is_exp = True
            possible_number.append(possible_char)
    

        possible_number_str = "".join(possible_number)
        if is_float or is_exp:
            return float(possible_number_str)
        return int(possible_number_str)

    if first_char == "{":
        for index in range(first_char_index, len(json_str)):
            char = json_str[index]

            if char == " ":
                continue

            if char == "{":
                if len(stack) > 0:
                    raise ParsingError("ha!")
                
                stack.append(char)
            
            elif char == "}":
                if not stack:
                    raise ParsingError("ha!")
            
                stack.pop()

            else:
                raise ParsingError("ha!")
            
        if stack:
            raise ParsingError("ha!")
    
        return {}
    
    raise ParsingError("ha!")
