from typing import Any
from ast_nodes import (
    Num, BinOp, Var,
    Assign, Print, ExprStmt,
    Program, Node,
    If, While, Block,
)


def evaluate(node: Node, env: dict[str, Any]):
    if isinstance(node, Program):
        result = None
        for stmt in node.statements:
            result = evaluate(stmt, env)
        return result
    if isinstance(node, Block):
        result = None
        for stmt in node.statements:
            result = evaluate(stmt, env)
        return result
    if isinstance(node, If):
        if evaluate(node.cond, env):
            return evaluate(node.then_block, env)
        if node.else_block is not None:
            return evaluate(node.else_block, env)
        return None
    if isinstance(node, While):
        while evaluate(node.cond, env):
            evaluate(node.body, env)
        return None
    if isinstance(node, Assign):
        env[node.name] = evaluate(node.expr, env)
        return None
    if isinstance(node, Print):
        print(evaluate(node.expr, env))
        return None
    if isinstance(node, ExprStmt):
        return evaluate(node.expr, env)
    if isinstance(node, Var):
        if node.name not in env:
            raise NameError(f"undefined variable: {node.name}")
        return env[node.name]
    if isinstance(node, Num):
        return node.value
    if isinstance(node, BinOp):
        left = evaluate(node.left, env)
        right = evaluate(node.right, env)
        if node.op == "+":
            return left + right
        if node.op == "-":
            return left - right
        if node.op == "*":
            return left * right
        if node.op == "/":
            return left / right
        if node.op == "==":
            return left == right
        if node.op == "!=":
            return left != right
        if node.op == "<":
            return left < right
        if node.op == ">":
            return left > right
        if node.op == "<=":
            return left <= right
        if node.op == ">=":
            return left >= right
        raise RuntimeError(f"unknown operator: {node.op}")
    raise RuntimeError(f"unknown node: {node}")
