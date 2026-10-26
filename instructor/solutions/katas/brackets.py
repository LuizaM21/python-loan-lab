"""Reference solution."""

from __future__ import annotations


def is_balanced(text: str) -> bool:
    """True when every (, [ and { is closed by the matching bracket in the right order.
    Other characters are ignored. Hint: a list used as a stack."""
    pairs = {")": "(", "]": "[", "}": "{"}
    stack: list[str] = []
    for char in text:
        if char in "([{":
            stack.append(char)
        elif char in pairs and (not stack or stack.pop() != pairs[char]):
            return False
    return not stack
