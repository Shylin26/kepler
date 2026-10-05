"""
Regression test for basic_sanity_check()'s runaway-kill handling (exit_code
-2). Confirms: (1) the success path still works -- this specifically guards
against the near-miss bug caught during development, where an edit
accidentally deleted the empty-output/traceback checks and the final
passed=True return entirely; (2) a runaway kill produces a distinct,
actionable reason rather than the generic non-zero-exit-code message.
"""

from agents.critic.critic_agent import basic_sanity_check

def test_success_path_still_works():
    result = basic_sanity_check({"exit_code": 0, "output": "hello world"})
    assert result["passed"] is True
    assert result["reason"] == "Passed basic sanity checks."
    print("PASS: success path intact.")

def test_empty_output_still_fails():
    result = basic_sanity_check({"exit_code": 0, "output": "   "})
    assert result["passed"] is False
    assert "no output" in result["reason"].lower()
    print("PASS: empty-output check intact.")

def test_traceback_still_fails():
    result = basic_sanity_check({"exit_code": 0, "output": "Traceback (most recent call last):\nValueError: bad"})
    assert result["passed"] is False
    assert "traceback" in result["reason"].lower()
    print("PASS: traceback check intact.")

def test_generic_nonzero_exit_unaffected():
    result = basic_sanity_check({"exit_code": 1, "output": "some error"})
    assert result["passed"] is False
    assert "Non-zero exit code: 1" in result["reason"]
    print("PASS: generic non-zero exit code handling unaffected.")

def test_runaway_kill_gives_actionable_reason():
    result = basic_sanity_check({
        "exit_code": -2,
        "output": "loss: nan\n" * 20,
        "runaway_info": {"runaway": True, "repeated_line": "loss: nan", "nan_related": True},
    })
    assert result["passed"] is False
    assert "runaway" in result["reason"].lower()
    assert "loss: nan" in result["reason"]
    assert "nan/inf-related" in result["reason"]
    print("PASS: runaway kill produces a distinct, actionable reason.")

if __name__ == "__main__":
    test_success_path_still_works()
    test_empty_output_still_fails()
    test_traceback_still_fails()
    test_generic_nonzero_exit_unaffected()
    test_runaway_kill_gives_actionable_reason()
    print("\nAll basic_sanity_check() tests passed.")