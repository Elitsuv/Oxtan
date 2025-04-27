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
            while i < len(code) and code[i].isalpha():
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
            tokens.append(code[start:i])
            i += 1
            continue
        if var in '()=' or '+-':
            tokens.append(var)
            i += 1
            continue
        print(f"Error: Invalid character '{var}' in OXTAN")
        return []
    return tokens

variables = {}

def parse(tokens):
    if not tokens:
        return None
    if len(tokens) == 3 and tokens[1] == "=":
        return {"type": "assign", "var": tokens[0], "value": tokens[2]}
    if len(tokens) == 3 and tokens[1] == "==":
        return {"type": "compare", "left": tokens[0], "right": tokens[2]}
    if len(tokens) == 3 and tokens[1] in ("+", "-"):
        return {"type": "math", "left": tokens[0], "op": tokens[1], "right": tokens[2]}
    if len(tokens) == 4 and tokens[0] == "say" and tokens[1] == "(" and tokens[3] == ")":
        return {"type": "say", "value": tokens[2]}
    print(f"Error: Invalid statement {tokens} in OXTAN")
    return None

def resolve(value):
    if value.isdigit():
        return int(value)
    return variables.get(value, None)

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
        left = resolve(ast["left"])
        right = resolve(ast["right"])
        if left is None or right is None:
            print(f"Error: Unknown variable in math operation")
            return
        if ast["op"] == "+":
            print(left + right)
        else:
            print(left - right)
    elif ast["type"] == "say":
        val = resolve(ast["value"])
        if val is None:
            val = ast["value"]
        print(val)

def oxtan_run():
    print("OXTAN Language (type 'exit' to quit, 'cmd' to show all commands)")
    commands = [
        "say('text') - Print text to the console",
        "x = value - Assign a value to a variable",
        "x == value - Compare a variable with a value",
        "x + y - Add two variables or values",
        "x - y - Subtract two variables or values"
    ]
    while True:
        try:
            code = input("> ")
            if code.lower() == "exit":
                break
            if code.lower() == "cmd":
                print("Available commands:")
                for command in commands:
                    print(f"  {command}")
                continue
            tokens = tokenize(code)
            if tokens:
                ast = parse(tokens)
                if ast:
                    execute(ast)
                else:
                    print("Wrong typo, Check out cmd")
            else:
                print("Wrong typo, Check out cmd")
        except KeyboardInterrupt:
            print("\nExiting OXTAN...")
            break

if __name__ == "__main__":
    oxtan_run()