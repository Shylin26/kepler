"""
check_generalization_scope() with multiple quotes. It must:
- flag a real cherry-pick (universal language, one quote covering 1 of 5 sibling lines)
- stay silent when the quotes cover every sibling line
- flag when the quotes cover only some of the sibling lines
- stay silent when the reasoning has no universal language
"""
from agents.analyst.analyst_agent import check_generalization_scope

OUTPUT = "\n".join(f"Seed {i}: steps to target = {400 + i}" for i in range(1, 6))
ALL = [f"Seed {i}: steps to target = {400 + i}" for i in range(1, 6)]
UNIVERSAL = "The method consistently reaches the target in fewer steps across all seeds."

def test_single_quote_cherry_pick_flagged():
    r = check_generalization_scope(UNIVERSAL, [ALL[2]], OUTPUT)
    assert r["checked"] is True and r.get("possible_cherry_pick") is True

def test_quotes_covering_all_siblings_not_flagged():
    r = check_generalization_scope(UNIVERSAL, ALL, OUTPUT)
    assert not r.get("possible_cherry_pick")

def test_partial_coverage_flagged():
    r = check_generalization_scope(UNIVERSAL, ALL[:2], OUTPUT)
    assert r.get("possible_cherry_pick") is True

def test_no_universal_language_not_checked():
    r = check_generalization_scope("Seed 3 reached the target in 403 steps.", [ALL[2]], OUTPUT)
    assert r["checked"] is False

if __name__ == "__main__":
    test_single_quote_cherry_pick_flagged()
    test_quotes_covering_all_siblings_not_flagged()
    test_partial_coverage_flagged()
    test_no_universal_language_not_checked()
    print("All generalization-scope multi-quote tests passed.")