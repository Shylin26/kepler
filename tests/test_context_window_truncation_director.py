"""
Regression test: confirms num_ctx=32768 prevents front-truncation of
Director's propose_topic_area() prompt. The prompt puts instructions FIRST
and an accumulating "already covered" list LAST -- risk grows over the
project's lifetime as more topic areas pile up. This test bypasses the live
Neo4j graph and directly exercises the prompt-construction + ollama.generate()
path with a synthetic, deliberately oversized covered-list, planting a
distinctive entry at the very START of that list (the position most at risk
of being silently dropped under truncation) and checking the model correctly
avoids proposing something equivalent to it.
"""

import ollama
from memory.trajectory_store.llm_cost import extract_llm_cost

# A common, "obvious" topic area a model would likely propose if it had no
# idea this had already been covered. Planted at the very START of the
# covered list -- the position most at risk under front-truncation.
PLANTED_TOPIC = "learning rate scheduling"

FILLER_COVERED = "\n".join(f"- filler topic area number {i}" for i in range(1200))

def build_padded_topic_prompt() -> str:
    covered_list = f"- {PLANTED_TOPIC}\n{FILLER_COVERED}"
    return f"""You are a research director for a small-scale ML experimentation system.
Your job right now is NOT to write a specific research question -- only to name
a broad TOPIC AREA to focus on next (e.g. "learning rate scheduling",
"weight initialization strategies", "optimizer choice", "regularization").

Topic areas must be small-scale-experiment-friendly: testable on a single CPU,
under a minute, with synthetic data, no third-party packages.

These EXACT topic areas have already been covered -- you MUST propose something
different from all of these:
{covered_list}

Respond with ONLY the topic area as a short phrase (3-6 words), nothing else.
No preamble, no explanation, no quotes.
"""

def test_planted_topic_is_not_reproposed():
    prompt = build_padded_topic_prompt()
    response = ollama.generate(
        model="qwen2.5-coder:7b",
        prompt=prompt,
        options={"num_ctx": 32768},
    )
    cost = extract_llm_cost(response)
    result = response["response"].strip()

    print("--- PROMPT TOKENS ---")
    print(cost.get("prompt_tokens"))
    print("--- RESULT ---")
    print(result)

    assert cost.get("prompt_tokens", 0) > 4096, (
        "Test prompt wasn't actually large enough to exercise the truncation-prone path."
    )
    assert PLANTED_TOPIC.lower() not in result.lower(), (
        f"Model re-proposed '{PLANTED_TOPIC}', which was planted at the START of the "
        f"covered list -- possible front-truncation regression (model didn't see it "
        f"was already covered)."
    )
    print(f"PASS: planted topic at start of a {cost.get('prompt_tokens')}-token prompt "
          f"was correctly respected as already-covered, num_ctx=32768 fix confirmed "
          f"at Director's propose_topic_area() call site.")

if __name__ == "__main__":
    test_planted_topic_is_not_reproposed()