from tokens import Token, TokenKind
from ast_nodes import (
    Num, BinOp, Var,
    Assign, Print, ExprStmt,
    Program, Node,
)


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

    def parse(self) -> Program:
        statements: list[Node] = []
        while self._peek().kind != TokenKind.EOF:
            statements.append(self._statement())
        return Program(statements)

    def _peek(self, offset: int = 0) -> Token:
        return self.tokens[self.pos + offset]

    def _advance(self) -> Token:
        t = self.tokens[self.pos]
        self.pos += 1
        return t

    def _expect(self, kind: TokenKind) -> Token:
        if self._peek().kind != kind:
            raise SyntaxError(f"expected {kind}, got {self._peek()}")
        return self._advance()

    def _statement(self) -> Node:
        t = self._peek()
        if t.kind == TokenKind.PRINT:
            return self._print_stmt()
        if t.kind == TokenKind.IDENT and self._peek(1).kind == TokenKind.EQUAL:
            return self._assign_stmt()
        return self._expr_stmt()

    def _print_stmt(self) -> Print:
        self._advance()
        self._expect(TokenKind.LPAREN)
        expr = self._expr()
        self._expect(TokenKind.RPAREN)
        self._consume_optional_semicolon()
        return Print(expr)

    def _assign_stmt(self) -> Assign:
        name = self._advance().value
        self._expect(TokenKind.EQUAL)
        expr = self._expr()
        self._consume_optional_semicolon()
        return Assign(name, expr)

    def _expr_stmt(self) -> ExprStmt:
        expr = self._expr()
        self._consume_optional_semicolon()
        return ExprStmt(expr)

    def _consume_optional_semicolon(self) -> None:
        if self._peek().kind == TokenKind.SEMICOLON:
            self._advance()

    def _expr(self) -> Node:
        node = self._term()
        while self._peek().kind in (TokenKind.PLUS, TokenKind.MINUS):
            op = "+" if self._advance().kind == TokenKind.PLUS else "-"
            node = BinOp(op, node, self._term())
        return node

    def _term(self) -> Node:
        node = self._factor()
        while self._peek().kind in (TokenKind.STAR, TokenKind.SLASH):
            op = "*" if self._advance().kind == TokenKind.STAR else "/"
            node = BinOp(op, node, self._factor())
        return node

    def _factor(self) -> Node:
        t = self._peek()
        if t.kind == TokenKind.NUMBER:
            self._advance()
            return Num(int(t.value))
        if t.kind == TokenKind.IDENT:
            self._advance()
            return Var(t.value)
        if t.kind == TokenKind.LPAREN:
            self._advance()
            node = self._expr()
            self._expect(TokenKind.RPAREN)
            return node
        raise SyntaxError(f"unexpected token: {t}")
