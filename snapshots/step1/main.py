from lexer import Lexer
from parser import Parser
from evaluator import evaluate


def run(source: str):
    tokens = Lexer(source).tokenize()
    tree = Parser(tokens).parse()
    return evaluate(tree)


def main():
    print("minilang step 1: calculator")
    print("Ctrl+C or Ctrl+D to exit")
    while True:
        try:
            line = input("> ")
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line.strip():
            continue
        try:
            print(run(line))
        except Exception as e:
            print(f"error: {e}")


if __name__ == "__main__":
    main()
