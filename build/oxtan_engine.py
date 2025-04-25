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
        if var in '()':
            tokens.append(var)
            i += 1
            continue
        print(f"Error: Invalid character '{var}' in OXTAN")
        return []
    return tokens

def parse(tokens):
    if len(tokens) != 4:
        print("Error: Wrong number of tokens in OXTAN")
        return None
    if tokens[0] != "say" or tokens[1] != "(" or tokens[3] != ")":
        print("Error: Must be say('text'), say(\"text\"), or say(number) in OXTAN")
        return None
    value = tokens[2]
    if value.isdigit():
        value = int(value)
    ast = {"type": "say", "value": value}
    return ast

def execute(ast):
    if ast and ast["type"] == "say":
        print(ast["value"])

def oxtan_run():
    print("OXTAN Language (type 'exit' to quit)")
    while True:
        try:
            code = input("> ")
            if code.lower() == "exit":
                break
            tokens = tokenize(code)
            if tokens:
                ast = parse(tokens)
                execute(ast)
        except KeyboardInterrupt:
            print("\nExiting OXTAN...")
            break

if __name__ == "__main__":
    oxtan_run()