import ollama
import json

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

Respond with ONLY a JSON object in this exact format:
{{"verdict": "supports" or "refutes" or "inconclusive", "reasoning": "one to two sentence explanation citing specific numbers from the output"}}
"""

    response = ollama.generate(model=model, prompt=prompt)
    raw = response["response"].strip()

    try:
        start = raw.index("{")
        end = raw.rindex("}") + 1
        parsed = json.loads(raw[start:end])
        return {
            "verdict": parsed.get("verdict", "inconclusive"),
            "reasoning": parsed.get("reasoning", "No reasoning given."),
        }
    except (ValueError, json.JSONDecodeError):
        return {"verdict": "inconclusive", "reasoning": f"Could not parse analyst response: {raw[:200]}"}


if __name__ == "__main__":
    result = analyze_result(
        hypothesis="Applying gradient clipping at a specific threshold consistently improves model performance on synthetic data for a simple linear regression task.",
        expected_outcome="The model trained with gradient clipping should show a consistent reduction in MSE loss over epochs, while the model without clipping may exhibit oscillations or divergence.",
        output="Theta without clipping: [0.017156616086403027, 2.0025443141855557]\nTheta with clipping: [0.6347624303780015, -0.5894226903910087]",
    )
    print(result)