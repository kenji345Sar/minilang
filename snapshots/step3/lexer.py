from tokens import Token, TokenKind


KEYWORDS = {
    "print": TokenKind.PRINT,
    "if": TokenKind.IF,
    "else": TokenKind.ELSE,
    "while": TokenKind.WHILE,
}


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
            elif ch.isalpha() or ch == "_":
                tokens.append(self._ident_or_keyword())
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
            elif ch == "{":
                tokens.append(Token(TokenKind.LBRACE))
                self.pos += 1
            elif ch == "}":
                tokens.append(Token(TokenKind.RBRACE))
                self.pos += 1
            elif ch == ";":
                tokens.append(Token(TokenKind.SEMICOLON))
                self.pos += 1
            elif ch == "=":
                if self._peek_char(1) == "=":
                    tokens.append(Token(TokenKind.EQEQ))
                    self.pos += 2
                else:
                    tokens.append(Token(TokenKind.EQUAL))
                    self.pos += 1
            elif ch == "!":
                if self._peek_char(1) == "=":
                    tokens.append(Token(TokenKind.BANGEQ))
                    self.pos += 2
                else:
                    raise SyntaxError("unexpected character: '!' (expected '!=')")
            elif ch == "<":
                if self._peek_char(1) == "=":
                    tokens.append(Token(TokenKind.LTEQ))
                    self.pos += 2
                else:
                    tokens.append(Token(TokenKind.LT))
                    self.pos += 1
            elif ch == ">":
                if self._peek_char(1) == "=":
                    tokens.append(Token(TokenKind.GTEQ))
                    self.pos += 2
                else:
                    tokens.append(Token(TokenKind.GT))
                    self.pos += 1
            else:
                raise SyntaxError(f"unexpected character: {ch!r}")
        tokens.append(Token(TokenKind.EOF))
        return tokens

    def _peek_char(self, offset: int) -> str | None:
        p = self.pos + offset
        if p < len(self.source):
            return self.source[p]
        return None

    def _number(self) -> Token:
        start = self.pos
        while self.pos < len(self.source) and self.source[self.pos].isdigit():
            self.pos += 1
        return Token(TokenKind.NUMBER, self.source[start:self.pos])

    def _ident_or_keyword(self) -> Token:
        start = self.pos
        while self.pos < len(self.source) and (
            self.source[self.pos].isalnum() or self.source[self.pos] == "_"
        ):
            self.pos += 1
        word = self.source[start:self.pos]
        if word in KEYWORDS:
            return Token(KEYWORDS[word], word)
        return Token(TokenKind.IDENT, word)
