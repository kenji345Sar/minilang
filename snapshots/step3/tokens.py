from dataclasses import dataclass
from enum import Enum, auto


class TokenKind(Enum):
    NUMBER = auto()
    IDENT = auto()
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    LPAREN = auto()
    RPAREN = auto()
    EQUAL = auto()
    SEMICOLON = auto()
    PRINT = auto()
    # step 3
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    LBRACE = auto()
    RBRACE = auto()
    EQEQ = auto()
    BANGEQ = auto()
    LT = auto()
    GT = auto()
    LTEQ = auto()
    GTEQ = auto()
    EOF = auto()


@dataclass
class Token:
    kind: TokenKind
    value: str | None = None
