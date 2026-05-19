from dataclasses import dataclass
from typing import Union, Optional


Node = Union[
    "Num", "BinOp", "Var",
    "Assign", "Print", "ExprStmt",
    "Program",
    "If", "While", "Block",
]


@dataclass
class Num:
    value: int


@dataclass
class BinOp:
    op: str
    left: Node
    right: Node


@dataclass
class Var:
    name: str


@dataclass
class Assign:
    name: str
    expr: Node


@dataclass
class Print:
    expr: Node


@dataclass
class ExprStmt:
    expr: Node


@dataclass
class Program:
    statements: list[Node]


@dataclass
class If:
    cond: Node
    then_block: Node
    else_block: Optional[Node]


@dataclass
class While:
    cond: Node
    body: Node


@dataclass
class Block:
    statements: list[Node]
