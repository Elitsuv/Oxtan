variables = {}

def tokenize(code):
    tokens = []
    i = 0
    while i < len(code):
        var = code[i]
        if var.isspace():
            i += 1
            continue
        if var.isalpha():
            start = i
            while i < len(code) and (code[i].isalpha() or code[i].isdigit()):
                i += 1
            tokens.append(code[start:i])
            continue
        if var.isdigit():
            start = i
            while i < len(code) and code[i].isdigit():
                i += 1
            tokens.append(code[start:i])
            continue
        if var in "'\"":
            quote = var
            i += 1
            start = i
            while i < len(code) and code[i] != quote:
                i += 1
            if i >= len(code):
                print("Error: Missing closing quote in OXTAN")
                return []
            tokens.append(code[start:i])  # Include the string as is, with spaces
            i += 1  # Skip the closing quote
            continue
        if var in '()=' or var in '+-*/':
            tokens.append(var)
            i += 1
            continue
        print(f"Error: Invalid character '{var}' in OXTAN")
        return []
    return tokens

def parse_expression(tokens, start=0):
    if start >= len(tokens):
        return None, start
    
    if tokens[start].isdigit() or tokens[start].isalpha():
        left = tokens[start]
        start += 1
        
        if start < len(tokens) and tokens[start] in '+-*/':
            op = tokens[start]
            start += 1
            if start < len(tokens) and (tokens[start].isdigit() or tokens[start].isalpha()):
                right = tokens[start]
                start += 1
                return {"type": "math", "left": left, "op": op, "right": right}, start
        return left, start
    
    return None, start

def parse(tokens):
    if not tokens:
        return None
    if len(tokens) == 3 and tokens[1] == "=":
        return {"type": "assign", "var": tokens[0], "value": tokens[2]}
    if len(tokens) == 3 and tokens[1] == "==":
        return {"type": "compare", "left": tokens[0], "right": tokens[2]}
    if len(tokens) == 3 and tokens[1] in ("+", "-", "*", "/"):
        return {"type": "math", "left": tokens[0], "op": tokens[1], "right": tokens[2]}
    if tokens[0] == "say" and tokens[1] == "(" and tokens[-1] == ")":
        inner_tokens = tokens[2:-1]
        if inner_tokens:
            if len(inner_tokens) == 1 and not (inner_tokens[0].isdigit() or inner_tokens[0] in '+-*/'):
                return {"type": "say", "value": inner_tokens[0]}
            expr, end = parse_expression(inner_tokens)
            if end == len(inner_tokens):
                return {"type": "say", "value": expr}
            else:
                print(f"Error: Invalid expression inside say: {' '.join(inner_tokens)}")
                return None
        else:
            return {"type": "say", "value": ""}
    print(f"Error: Invalid statement {' '.join(tokens)} in OXTAN")
    return None

def resolve(value):
    if isinstance(value, dict) and value["type"] == "math":
        left = resolve(value["left"])
        right = resolve(value["right"])
        if left is None or right is None:
            print(f"Error: Unknown variable in math operation")
            return None
        if value["op"] == "+":
            return left + right
        elif value["op"] == "-":
            return left - right
        elif value["op"] == "*":
            return left * right
        elif value["op"] == "/":
            if right == 0:
                print("Error: Division by zero")
                return None
            return left / right
    if isinstance(value, str):
        if value.isdigit():
            return int(value)
        return variables.get(value, value)  # Return string literal or variable value
    return value

def execute(ast):
    if not ast:
        return
    if ast["type"] == "assign":
        val = resolve(ast["value"])
        if val is None:
            print(f"Error: Cannot assign unknown value '{ast['value']}'")
            return
        variables[ast["var"]] = val
        print(f"Assigned {ast['var']} = {val}")
    elif ast["type"] == "compare":
        left = resolve(ast["left"])
        right = resolve(ast["right"])
        print(left == right)
    elif ast["type"] == "math":
        result = resolve(ast)
        if result is not None:
            print(result)
    elif ast["type"] == "say":
        val = resolve(ast["value"])
        if val is None:
            print(f"Error: Cannot say unknown value")
            return
        print(val)

def oxtan_run():
    print("OXTAN Language (type 'exit' to quit, 'cmd' to show all commands)")
    commands = [
        "say('text') - Print text to the console",
        "say(x + y) - Print result of expression",
        "x = value - Assign a value to a variable",
        "x == value - Compare a variable with a value",
        "x + y - Add two variables or values",
        "x - y - Subtract two variables or values",
        "x * y - Multiply two variables or values",
        "x / y - Divide two variables or values"
    ]
    while True:
        try:
            code = input("> ")
            if code.lower() == "exit":
                break
            if code.lower() == "cmd":
                print("Available commands:")
                for command in commands:
                    print(f"{command}")
                continue
            tokens = tokenize(code)
            if tokens:
                ast = parse(tokens)
                if ast:
                    execute(ast)
                else:
                    print("Error: Invalid syntax. Type 'cmd' for help.")
            else:
                print("Error: Invalid input. Type 'cmd' for help.")
        except KeyboardInterrupt:
            print("\nExiting OXTAN...")
            break

if __name__ == "__main__":
    oxtan_run()