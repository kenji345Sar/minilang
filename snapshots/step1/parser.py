from tokens import Token, TokenKind
from ast_nodes import Num, BinOp, Node


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

    def parse(self) -> Node:
        return self._expr()

    def _peek(self) -> Token:
        return self.tokens[self.pos]

    def _advance(self) -> Token:
        t = self.tokens[self.pos]
        self.pos += 1
        return t

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
        if t.kind == TokenKind.LPAREN:
            self._advance()
            node = self._expr()
            if self._peek().kind != TokenKind.RPAREN:
                raise SyntaxError("expected ')'")
            self._advance()
            return node
        raise SyntaxError(f"unexpected token: {t}")
