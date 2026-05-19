from tokens import Token, TokenKind


class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.pos = 0

    def tokenize(self) -> list[Token]:
        tokens: list[Token] = []
        while self.pos < len(self.source):
            ch = self.source[self.pos]
            if ch.isspace():
                self.pos += 1
            elif ch.isdigit():
                tokens.append(self._number())
            elif ch == "+":
                tokens.append(Token(TokenKind.PLUS))
                self.pos += 1
            elif ch == "-":
                tokens.append(Token(TokenKind.MINUS))
                self.pos += 1
            elif ch == "*":
                tokens.append(Token(TokenKind.STAR))
                self.pos += 1
            elif ch == "/":
                tokens.append(Token(TokenKind.SLASH))
                self.pos += 1
            elif ch == "(":
                tokens.append(Token(TokenKind.LPAREN))
                self.pos += 1
            elif ch == ")":
                tokens.append(Token(TokenKind.RPAREN))
                self.pos += 1
            else:
                raise SyntaxError(f"unexpected character: {ch!r}")
        tokens.append(Token(TokenKind.EOF))
        return tokens

    def _number(self) -> Token:
        start = self.pos
        while self.pos < len(self.source) and self.source[self.pos].isdigit():
            self.pos += 1
        return Token(TokenKind.NUMBER, self.source[start:self.pos])
