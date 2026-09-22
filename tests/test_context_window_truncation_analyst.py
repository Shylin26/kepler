"""
Regression test: confirms num_ctx=32768 prevents front-truncation of
Analyst's analyze_result() prompt. hypothesis/expected_outcome come FIRST,
output comes LAST -- risk is that a large output pushes the hypothesis out.
Filler is deliberately inert (no trend, no story) so it can't compete
narratively with the real hypothesis/result -- isolates the truncation
question cleanly.
"""

import ollama
from agents.analyst.analyst_agent import analyze_result
from memory.trajectory_store.llm_cost import extract_llm_cost

HYPOTHESIS = "Doubling the batch size from 32 to 64 reduces final training loss by at least 10%."
EXPECTED_OUTCOME = "Final loss with batch size 64 should be at least 10% lower than with batch size 32."
REAL_RESULT_LINE = "Batch size 32: final_loss=0.4213 | Batch size 64: final_loss=0.4599"

# Inert filler -- no numeric trend, no narrative, just bulk.
FILLER_OUTPUT = "\n".join(f"[log line {i}] worker heartbeat ok" for i in range(1, 2500))

def build_padded_output() -> str:
    return f"{REAL_RESULT_LINE}\n{FILLER_OUTPUT}"

def check_prompt_size():
    """Directly measure token count for this exact prompt shape, independent
    of analyze_result()'s return value, since it doesn't expose cost."""
    output = build_padded_output()
    prompt = f"""You are a careful research analyst. Given a hypothesis, what
result was expected if the hypothesis were true, and the actual output of the
experiment, determine whether the result SUPPORTS the hypothesis, REFUTES it,
or is INCONCLUSIVE.

Hypothesis:
{HYPOTHESIS}

Expected outcome if the hypothesis is true:
{EXPECTED_OUTCOME}

Actual experiment output:
{output}
"""
    response = ollama.generate(model="qwen2.5-coder:7b", prompt=prompt, options={"num_ctx": 32768})
    cost = extract_llm_cost(response)
    print(f"[prompt size check] prompt_tokens: {cost.get('prompt_tokens')}")
    return cost.get("prompt_tokens", 0)

def test_hypothesis_and_result_both_survive_long_output():
    prompt_tokens = check_prompt_size()
    assert prompt_tokens > 4096, (
        "Test prompt wasn't actually large enough to exercise the truncation-prone path."
    )

    output = build_padded_output()
    result = analyze_result(HYPOTHESIS, EXPECTED_OUTCOME, output)

    print("--- VERDICT ---")
    print(result)

    assert result["verdict"] == "refutes", (
        f"Expected 'refutes' (loss increased, contradicting the hypothesis), "
        f"got '{result['verdict']}' -- possible truncation of hypothesis or "
        f"the real result line."
    )
    assert "0.4599" in result.get("supporting_quote", "") or "0.4213" in result.get("supporting_quote", ""), (
        "Supporting quote doesn't reference the real result numbers -- "
        "possible truncation."
    )
    print(f"PASS: at {prompt_tokens} prompt tokens, Analyst correctly judged the real "
          f"hypothesis against the real result line -- num_ctx=32768 fix confirmed "
          f"at Analyst's analyze_result() call site.")

if __name__ == "__main__":
    test_hypothesis_and_result_both_survive_long_output()