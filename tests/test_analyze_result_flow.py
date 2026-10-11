"""
End-to-end flow of analyze_result() with a stubbed LLM. Guards against
indentation/early-return slips that unit tests of the helper functions miss
(a mis-indented generalization_check line once made analyze_result() crash
whenever the direction check didn't fire).
"""
import json
from unittest.mock import patch
import agents.analyst.analyst_agent as aa

OUTPUT = "Seed 1: steps = 401\nSeed 2: steps = 402\n"

def _fake(payload):
    return {"response": json.dumps(payload), "total_duration": 1, "load_duration": 0,
            "prompt_eval_count": 1, "eval_count": 1}

def _run(payload):
    with patch.object(aa.ollama, "generate", return_value=_fake(payload)):
        return aa.analyze_result("h", "e", OUTPUT)

def test_no_numbers_in_reasoning_still_returns_full_dict():
    r = _run({"verdict": "supports", "reasoning": "It looks better.",
              "supporting_quotes": ["Seed 1: steps = 401"]})
    assert r["verdict"] == "supports"
    assert "generalization_check" in r and "direction_check" in r

def test_spliced_quote_is_downgraded():
    r = _run({"verdict": "supports", "reasoning": "x",
              "supporting_quotes": ["Seed 1: steps = 401\nSeed 2: steps = 402\nextra"]})
    assert r["verdict"] == "inconclusive" and "rejected_quotes" in r

def test_honest_inconclusive_with_no_quotes_not_downgraded():
    r = _run({"verdict": "inconclusive", "reasoning": "not enough info",
              "supporting_quotes": []})
    assert r["verdict"] == "inconclusive" and "DOWNGRADED" not in r["reasoning"]

if __name__ == "__main__":
    test_no_numbers_in_reasoning_still_returns_full_dict()
    test_spliced_quote_is_downgraded()
    test_honest_inconclusive_with_no_quotes_not_downgraded()
    print("All analyze_result flow tests passed.")