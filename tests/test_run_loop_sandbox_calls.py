import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import patch
from types import SimpleNamespace
import run_loop

# Minimal fake spec -- we don't need a real ExperimentSpec/Pydantic object,
# just something with the two attributes run_with_self_correction touches.
fake_spec = SimpleNamespace(
    task_description="Write a function that adds two numbers.",
    compute_budget_seconds=30,
)

def test_syntax_failure_skips_sandbox():
    """If syntax check fails, run_code_in_sandbox should NOT be called at all."""
    with patch("run_loop.generate_code", return_value="def broken(:\n    pass"), \
         patch("run_loop.run_code_in_sandbox") as mock_sandbox, \
         patch("run_loop.basic_sanity_check", return_value={"passed": False, "reason": "syntax error"}):
        run_loop.run_with_self_correction(fake_spec, max_attempts=1)
    print(f"syntax failure case: run_code_in_sandbox called {mock_sandbox.call_count} times (expect 0)")

def test_valid_syntax_calls_sandbox_once():
    """If syntax check passes, run_code_in_sandbox should be called exactly
    ONCE per attempt -- not twice, which was the bug."""
    with patch("run_loop.generate_code", return_value="print('hello')"), \
         patch("run_loop.run_code_in_sandbox", return_value={"exit_code": 0, "output": "hello"}) as mock_sandbox, \
         patch("run_loop.basic_sanity_check", return_value={"passed": True}):
        run_loop.run_with_self_correction(fake_spec, max_attempts=1)
    print(f"valid syntax case: run_code_in_sandbox called {mock_sandbox.call_count} times (expect 1)")

if __name__ == "__main__":
    test_syntax_failure_skips_sandbox()
    test_valid_syntax_calls_sandbox_once()