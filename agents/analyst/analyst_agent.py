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
        direction_check = check_numeric_direction(reasoning)
        if direction_check["checked"] and not direction_check["consistent"]:
            print(f"--- WARNING: possible numeric direction inconsistency in Analyst reasoning: {direction_check['reason']} ---")
        generalization_check = check_generalization_scope(reasoning, quote, output)
        if generalization_check["checked"] and generalization_check.get("possible_cherry_pick"):
            print(f"--- WARNING: possible cherry-picking in Analyst reasoning: {generalization_check['reason']} ---")
        return {
            "verdict": verdict,
            "reasoning": reasoning,
            "supporting_quote": quote,
            "direction_check": direction_check,
            "generalization_check": generalization_check,
        }
    except (ValueError, json.JSONDecodeError):
        return {"verdict": "inconclusive", "reasoning": f"Could not parse analyst response: {raw[:200]}"}
    
def _normalize_for_grounding(text: str) -> str:
    """Narrow, explicit normalization for grounding comparison ONLY -- not
    used anywhere else. Deliberately does NOT touch numeric formatting
    (e.g. 0.57 vs 0.570 are left distinct) since collapsing numeric
    precision could mask a real discrepancy. Only handles whitespace/
    line-break variance and a small set of trailing punctuation that
    LLMs commonly add when copying a quote."""
    text = text.strip().lower()
    text = re.sub(r"\s+", " ", text)          # collapse all whitespace/newlines to single space
    text = text.rstrip(".,%")                  # strip a small explicit set of trailing punctuation
    return text

def check_grounding(supporting_quote: str, output: str) -> dict:
    """Verify that the Analyst's supporting_quote is a (normalized) exact
    substring of the real experiment output -- not paraphrased, not
    invented. See _normalize_for_grounding for exactly what counts as
    'the same' -- deliberately narrow, not fuzzy matching."""
    quote_clean = supporting_quote.strip()
    if not quote_clean:
        return {"grounded": False, "reason": "No supporting quote provided."}
    if _normalize_for_grounding(quote_clean) in _normalize_for_grounding(output):
        return {"grounded": True, "reason": None}
    return {"grounded": False, "reason": f"Quote not found verbatim (even after normalization) in output: '{quote_clean[:100]}'"}

def check_numeric_direction(reasoning: str) -> dict:
    """Heuristic check: if reasoning text contains an explicit numeric
    comparison (two numbers with a directional word like higher/lower/
    more/less/greater/smaller between them), verify the claimed direction
    matches the actual arithmetic relationship between the first two
    numbers found.

    Deliberately narrow -- built to catch the exact failure pattern seen
    in issue #13 (claiming a lower number is 'higher'), not a general
    logic checker. Does NOT catch cherry-picking (see #13 B2) or
    self-contradictory reasoning using both directional word types.
    Returns checked=False when there's nothing clear to check -- that is
    NOT the same as confirming the reasoning is correct.
    """
    HIGHER_WORDS = ["higher", "greater", "more", "increase", "improved", "better", "exceeds"]
    LOWER_WORDS = ["lower", "smaller", "less", "decrease", "worse", "below", "reduced"]

    numbers = [float(m) for m in re.findall(r"-?\d+\.?\d*", reasoning)]
    if len(numbers) < 2:
        return {"checked": False, "reason": "Fewer than 2 numbers found in reasoning."}

    text_lower = reasoning.lower()
    found_higher = any(w in text_lower for w in HIGHER_WORDS)
    found_lower = any(w in text_lower for w in LOWER_WORDS)

    if found_higher and found_lower:
        return {"checked": False, "reason": "Both higher- and lower-direction words present -- ambiguous, skipping."}
    if not found_higher and not found_lower:
        return {"checked": False, "reason": "No clear directional comparison word found."}

    a, b = numbers[0], numbers[1]
    if a == b:
        return {"checked": False, "reason": f"First two numbers ({a}, {b}) are equal -- no direction to check."}

    actual_direction = "higher" if a > b else "lower"
    claimed_direction = "higher" if found_higher else "lower"
    consistent = actual_direction == claimed_direction
    return {
        "checked": True,
        "consistent": consistent,
        "reason": None if consistent else f"Reasoning claims '{claimed_direction}' but first two numbers found ({a} then {b}) are actually {actual_direction} in that order.",
    }

def check_generalization_scope(reasoning: str, quote: str, output: str) -> dict:
    """Heuristic check: if reasoning uses universal/consistency language
    (e.g. 'consistently', 'across all', 'every case') while the quoted
    evidence represents only one of several structurally similar data
    points in the real output, flag it as a possible cherry-pick.

    Does NOT determine whether the generalization is actually true --
    only whether the Analyst appears to have looked at all comparable
    evidence before making a universal claim. A pass here is not proof
    the reasoning is correct, only that it isn't obviously cherry-picked
    by this narrow test.
    """
    UNIVERSAL_WORDS = ["consistently", "across all", "every case", "in every",
                        "all seeds", "all cases", "always", "invariably",
                        "without exception", "in all"]

    text_lower = reasoning.lower()
    uses_universal_language = any(w in text_lower for w in UNIVERSAL_WORDS)
    if not uses_universal_language:
        return {"checked": False, "reason": "No universal/consistency language found in reasoning."}

    quote_clean = quote.strip()
    if not quote_clean:
        return {"checked": False, "reason": "No quote to compare against."}

    def template(line):
        return re.sub(r"-?\d+\.?\d*", "N", line.strip())

    quote_template = template(quote_clean)
    output_lines = [l for l in output.split("\n") if l.strip()]
    sibling_lines = [l for l in output_lines if template(l) == quote_template]

    if len(sibling_lines) < 2:
        return {"checked": False, "reason": "No structurally similar sibling lines found in output -- nothing to compare against."}

    return {
        "checked": True,
        "possible_cherry_pick": True,
        "reason": f"Reasoning uses universal language ('{[w for w in UNIVERSAL_WORDS if w in text_lower][0]}') but only cites 1 of {len(sibling_lines)} structurally similar data points in the output.",
        "sibling_count": len(sibling_lines),
    }  
if __name__ == "__main__":
    result = analyze_result(
        hypothesis="Adversarial training improves model robustness compared to standard training.",
        expected_outcome="The adversarially trained model should show more stable accuracy under small perturbations.",
        output="LR=0.01 Accuracy: 1.00\nLR=0.1 Accuracy: 1.00\nAdversarial Accuracy: 0.57",
    )
    print(result)
