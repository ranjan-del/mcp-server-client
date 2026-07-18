"""Tests for the calculator tool: correctness and safety."""

import pytest

from server.tools.calculator import CalculatorError, calculate


@pytest.mark.parametrize(
    "expression, expected",
    [
        ("2 + 3", 5),
        ("2 + 3 * 4", 14),          # precedence
        ("(2 + 3) * 4", 20),        # parentheses
        ("10 / 4", 2.5),
        ("10 // 3", 3),
        ("10 % 3", 1),
        ("2 ** 10", 1024),
        ("-5 + 2", -3),             # unary minus
        ("+7", 7),                  # unary plus
    ],
)
def test_calculate_correctness(expression, expected):
    assert calculate(expression) == expected


def test_division_by_zero():
    with pytest.raises(CalculatorError):
        calculate("1 / 0")


def test_rejects_names_and_calls():
    # These would be dangerous under eval(); the AST whitelist must reject them.
    for bad in ["__import__('os')", "x + 1", "os.system('ls')", "print(1)"]:
        with pytest.raises(CalculatorError):
            calculate(bad)


def test_rejects_empty_and_garbage():
    with pytest.raises(CalculatorError):
        calculate("")
    with pytest.raises(CalculatorError):
        calculate("2 +")
