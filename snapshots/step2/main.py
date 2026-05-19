from typing import Any
from lexer import Lexer
from parser import Parser
from evaluator import evaluate
from ast_nodes import ExprStmt


def run(source: str, env: dict[str, Any]):
    tokens = Lexer(source).tokenize()
    program = Parser(tokens).parse()
    result = evaluate(program, env)
    # REPL 表示：単一の式文（print なし）なら値を出す
    if (
        len(program.statements) == 1
        and isinstance(program.statements[0], ExprStmt)
        and result is not None
    ):
        print(result)


def main():
    print("minilang step 2: variables and print")
    print("type 'exit' or 'quit' to leave (Ctrl+C / Ctrl+D も可)")
    env: dict[str, Any] = {}
    while True:
        try:
            line = input("> ")
        except (EOFError, KeyboardInterrupt):
            print()
            break
        stripped = line.strip().rstrip(";").strip()
        if stripped in ("exit", "quit"):
            break
        if not line.strip():
            continue
        try:
            run(line, env)
        except Exception as e:
            print(f"error: {e}")


if __name__ == "__main__":
    main()
