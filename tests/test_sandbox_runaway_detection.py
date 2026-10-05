"""
Regression + feature test for execution/sandbox/executor.py's runaway
detection. Test 1 confirms normal script execution is unaffected by the
polling rewrite. Test 2 confirms a script that gets stuck printing the same
line repeatedly is killed BEFORE the full timeout elapses, not after --
this is the actual "fail fast" behavior, not just post-hoc detection.
"""

import time
from execution.sandbox.executor import run_code_in_sandbox

def test_normal_script_unaffected():
    code = "print('hello world')"
    result = run_code_in_sandbox(code, timeout=10)
    print("--- NORMAL SCRIPT RESULT ---")
    print(result)

    assert result["exit_code"] == 0, f"Expected exit_code 0, got {result['exit_code']}"
    assert "hello world" in result["output"]
    assert result["killed_early_for_runaway"] is False
    assert result["duration_seconds"] < 5, (
        "Normal script took suspiciously long -- polling overhead may be too high."
    )
    print("PASS: normal script runs correctly, unaffected by polling rewrite.")


def test_runaway_script_killed_early():
    # A script that would loop for a very long time printing the same line.
    # If runaway detection works, this should be killed well before the
    # 30-second timeout -- proving genuine fail-fast behavior, not just
    # post-hoc detection after the full timeout elapses.
    code = """
while True:
    print("loss: nan")
"""
    timeout = 30
    result = run_code_in_sandbox(code, timeout=timeout)
    print("--- RUNAWAY SCRIPT RESULT ---")
    print(result)

    assert result["killed_early_for_runaway"] is True, (
        "Runaway script was NOT flagged as killed early -- detection failed."
    )
    assert result["exit_code"] == -2, f"Expected exit_code -2, got {result['exit_code']}"
    assert result["runaway_info"]["nan_related"] is True, (
        "Expected nan_related=True given the repeated line contains 'nan'."
    )
    assert result["duration_seconds"] < timeout - 5, (
        f"Took {result['duration_seconds']}s against a {timeout}s timeout -- "
        f"this isn't actually failing fast, just barely beating the timeout."
    )
    print(f"PASS: runaway script killed early at {result['duration_seconds']}s "
          f"(vs {timeout}s full timeout) -- genuine fail-fast confirmed, not post-hoc detection.")


if __name__ == "__main__":
    test_normal_script_unaffected()
    test_runaway_script_killed_early()