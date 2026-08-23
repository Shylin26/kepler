import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.coder.coder_agent import check_syntax

cases = [
    ("valid code", "print('hello')", True),
    ("simple syntax error", "def broken(:\n    pass", False),
    ("null byte in source", "print('hi')\x00", "UNKNOWN -- does this crash uncaught?"),
    ("deeply nested parens (5000 levels)", "(" * 5000 + "1" + ")" * 5000, "UNKNOWN -- does this crash uncaught (RecursionError)?"),
]

for label, code, expected in cases:
    try:
        result = check_syntax(code)
        print(f"{label:40s} -> {result}  (expected: {expected})")
    except Exception as e:
        print(f"{label:40s} -> CRASHED UNCAUGHT: {type(e).__name__}: {e}  (expected: {expected})")