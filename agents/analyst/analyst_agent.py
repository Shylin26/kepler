import ollama
import json
import re

def analyze_result(hypothesis: str, expected_outcome: str, output: str, model: str = "qwen2.5-coder:7b") -> dict:
    """Ask an LLM to judge whether an experiment's actual output supports,
    refutes, or is inconclusive relative to the stated hypothesis."""

    prompt = f"""You are a careful research analyst. Given a hypothesis, what
result was expected if the hypothesis were true, and the actual output of the
experiment, determine whether the result SUPPORTS the hypothesis, REFUTES it,
or is INCONCLUSIVE (e.g. the effect is present but too small/noisy to tell,
or the output doesn't contain the information needed to judge).

Hypothesis:
{hypothesis}

Expected outcome if the hypothesis is true:
{expected_outcome}

Actual experiment output:
{output}

Be skeptical and precise. Do not assume the hypothesis is true just because
the code ran successfully -- look at the actual numbers.

You must support your verdict with a DIRECT QUOTE copied exactly, character-
for-character, from the actual experiment output above. Do not paraphrase or
summarize the quote -- copy it verbatim. If you cannot find a exact substring
in the output that supports your verdict, you must respond with "inconclusive".

Respond with ONLY a JSON object in this exact format:
{{"verdict": "supports" or "refutes" or "inconclusive", "reasoning": "one to two sentence explanation", "supporting_quote": "exact verbatim substring copied from the output above"}}
"""

    response = ollama.generate(model=model, prompt=prompt)
    raw = response["response"].strip()

    try:
        start = raw.index("{")
        end = raw.rindex("}") + 1
        parsed = json.loads(raw[start:end])
        verdict = parsed.get("verdict", "inconclusive")
        reasoning = parsed.get("reasoning", "No reasoning given.")
        quote = parsed.get("supporting_quote", "")

        grounding = check_grounding(quote, output)
        if not grounding["grounded"]:
            return {
                "verdict": "inconclusive",
                "reasoning": f"[DOWNGRADED: {grounding['reason']}] Original reasoning: {reasoning}",
            }

        return {"verdict": verdict, "reasoning": reasoning, "supporting_quote": quote}
    except (ValueError, json.JSONDecodeError):
        return {"verdict": "inconclusive", "reasoning": f"Could not parse analyst response: {raw[:200]}"}
def check_grounding(supporting_quote: str, output: str) -> dict:
    """Verify that the Analyst's supporting_quote is an exact substring of
    the real experiment output -- not paraphrased, not invented."""
    quote_clean = supporting_quote.strip()
    if not quote_clean:
        return {"grounded": False, "reason": "No supporting quote provided."}

    if quote_clean in output:
        return {"grounded": True, "reason": None}

    return {"grounded": False, "reason": f"Quote not found verbatim in output: '{quote_clean[:100]}'"}

if __name__ == "__main__":
    result = analyze_result(
        hypothesis="Adversarial training improves model robustness compared to standard training.",
        expected_outcome="The adversarially trained model should show more stable accuracy under small perturbations.",
        output="LR=0.01 Accuracy: 1.00\nLR=0.1 Accuracy: 1.00\nAdversarial Accuracy: 0.57",
    )
    print(result)