"""Calculator tool.

MEMORY.md checklist: MCP Server tools -> calculator.

Design note
-----------
The whole point of this tool is *safe* arithmetic. A naive implementation would
call ``eval(expression)`` -- but that hands the caller the full power of Python
(imports, attribute access, ``__import__('os').system(...)`` and so on). Because
an MCP server runs input that ultimately comes from an LLM/client, that would be
a genuine remote-code-execution hole.

Instead we parse the expression into an Abstract Syntax Tree with ``ast.parse``
and then walk that tree ourselves, allowing ONLY a small whitelist of node
types (numbers, the basic operators, unary minus/plus and parentheses).
Anything else -- names, calls, attribute access -- is rejected. That gives a
real expression evaluator with none of ``eval``'s danger.
"""

from __future__ import annotations

import ast
import operator

# Whitelist of binary operators. Maps AST node type -> the callable that runs it.
_BINARY_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

# Whitelist of unary operators (e.g. the minus in "-3").
_UNARY_OPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


class CalculatorError(ValueError):
    """Raised when an expression is invalid or uses disallowed syntax."""


def _eval_node(node: ast.AST) -> float:
    """Recursively evaluate a single whitelisted AST node.

    Any node type that is not explicitly allowed raises ``CalculatorError`` --
    this is the security boundary that keeps arbitrary code from running.
    """
    # A numeric literal, e.g. 2 or 3.5
    if isinstance(node, ast.Constant):
        # bool is a subclass of int, so exclude True/False explicitly.
        if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
            raise CalculatorError(f"Only numbers are allowed, got {node.value!r}")
        return node.value

    # A binary operation, e.g. 2 + 3
    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in _BINARY_OPS:
            raise CalculatorError(f"Operator {op_type.__name__} is not allowed")
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        try:
            return _BINARY_OPS[op_type](left, right)
        except ZeroDivisionError as exc:
            raise CalculatorError("Division by zero") from exc

    # A unary operation, e.g. -3
    if isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in _UNARY_OPS:
            raise CalculatorError(f"Unary operator {op_type.__name__} is not allowed")
        return _UNARY_OPS[op_type](_eval_node(node.operand))

    # Anything else (Name, Call, Attribute, Subscript, ...) is rejected on purpose.
    raise CalculatorError(f"Disallowed expression element: {type(node).__name__}")


def calculate(expression: str) -> float:
    """Safely evaluate an arithmetic ``expression`` and return the numeric result.

    Supports ``+ - * / // % **``, parentheses and unary minus/plus.

    >>> calculate("2 + 3 * 4")
    14
    >>> calculate("(1 + 2) ** 3")
    27
    """
    if not isinstance(expression, str) or not expression.strip():
        raise CalculatorError("Expression must be a non-empty string")

    try:
        # mode="eval" parses a single expression (not statements), which already
        # rules out assignments, imports, semicolons, etc.
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise CalculatorError(f"Invalid syntax: {exc.msg}") from exc

    return _eval_node(tree.body)


def register(mcp) -> None:
    """Expose :func:`calculate` as an MCP tool on the given FastMCP server."""

    @mcp.tool()
    def calculator(expression: str) -> str:
        """Evaluate a basic arithmetic expression (e.g. "2 + 3 * 4").

        Supports + - * / // % ** and parentheses. Rejects any non-arithmetic
        input, so it is safe to expose to untrusted callers.
        """
        result = calculate(expression)
        return f"{expression} = {result}"
