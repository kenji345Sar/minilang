from dataclasses import dataclass
from typing import Union


Node = Union[
    "Num", "BinOp", "Var",
    "Assign", "Print", "ExprStmt",
    "Program",
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
