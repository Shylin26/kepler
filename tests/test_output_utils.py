from agents.output_utils import cap_output

def test_short_unchanged():
    assert cap_output("abc") == "abc"

def test_long_keeps_head_tail_and_marker():
    s = "HEAD" + "x" * 50000 + "TAIL"
    r = cap_output(s)
    assert r.startswith("HEAD") and r.endswith("TAIL")
    assert "characters omitted" in r
    assert len(r) < 24100

if __name__ == "__main__":
    test_short_unchanged()
    test_long_keeps_head_tail_and_marker()
    print("output_utils tests passed")