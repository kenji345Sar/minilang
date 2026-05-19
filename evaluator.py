from ast_nodes import Num, BinOp, Node


def evaluate(node: Node):
    if isinstance(node, Num):
        return node.value
    if isinstance(node, BinOp):
        left = evaluate(node.left)
        right = evaluate(node.right)
        if node.op == "+":
            return left + right
        if node.op == "-":
            return left - right
        if node.op == "*":
            return left * right
        if node.op == "/":
            return left / right
        raise RuntimeError(f"unknown operator: {node.op}")
    raise RuntimeError(f"unknown node: {node}")
