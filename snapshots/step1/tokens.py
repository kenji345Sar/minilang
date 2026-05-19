from dataclasses import dataclass
from enum import Enum, auto


class TokenKind(Enum):
    NUMBER = auto()
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    LPAREN = auto()
    RPAREN = auto()
    EOF = auto()


@dataclass
class Token:
    kind: TokenKind
    value: str | None = None
