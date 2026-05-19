from dataclasses import dataclass
from typing import Union


Node = Union["Num", "BinOp"]


@dataclass
class Num:
    value: int


@dataclass
class BinOp:
    op: str
    left: Node
    right: Node
