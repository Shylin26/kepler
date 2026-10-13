"""
basic_sanity_check() must surface the exception line even when the output
is long and the traceback is at the start or the end.
"""
from agents.critic.critic_agent import basic_sanity_check

TB = ('Traceback (most recent call last):\n  File "<string>", line 25, in <module>\n'
      '  File "<string>", line 11, in gradient_descent\n  File "<string>", line 11, in <listcomp>\n'
      '  File "<string>", line 11, in <genexpr>\n')
LONG = "".join(f"Iteration {i}, Loss = {i}.5\n" for i in range(200))

def test_traceback_first_error_line_kept():
    out = TB + "OverflowError: (34, 'Numerical result out of range')\n" + LONG
    r = basic_sanity_check({"exit_code": 1, "output": out})
    assert "OverflowError" in r["reason"]

def test_traceback_last_error_line_kept():
    out = LONG + TB + "NameError: name 'k' is not defined\n"
    r = basic_sanity_check({"exit_code": 1, "output": out})
    assert "NameError" in r["reason"]

def test_short_output_unchanged():
    r = basic_sanity_check({"exit_code": 1, "output": "boom"})
    assert "boom" in r["reason"]

def test_success_and_runaway_unchanged():
    assert basic_sanity_check({"exit_code": 0, "output": "ok"})["passed"] is True
    r = basic_sanity_check({"exit_code": -2, "output": "x",
                            "runaway_info": {"repeated_line": "nan", "nan_related": True}})
    assert "runaway" in r["reason"].lower()

if __name__ == "__main__":
    test_traceback_first_error_line_kept()
    test_traceback_last_error_line_kept()
    test_short_output_unchanged()
    test_success_and_runaway_unchanged()
    print("All critic error-feedback tests passed.")