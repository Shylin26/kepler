from run_loop import build_retry_prompt

def test_prompt_contents_and_order():
    p = build_retry_prompt("TASK TEXT", "print(1)", "NameError: name 'math' is not defined")
    assert p.startswith("TASK TEXT")
    assert "print(1)" in p
    assert "NameError: name 'math' is not defined" in p
    assert "Do not repeat it" in p

if __name__ == "__main__":
    test_prompt_contents_and_order()
    print("retry prompt test passed")