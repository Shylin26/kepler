"""
Regression test: confirms num_ctx=32768 prevents front-truncation of
Coder's generate_code() prompt, specifically simulating the retry-prompt
shape (task_description + previous failed code + critic reason) where
task_description sits first and is at risk of being silently dropped.
"""

from agents.coder.coder_agent import generate_code, check_syntax

# A unique, unambiguous marker placed at the very start of the task
# description -- if truncation drops the beginning, this instruction
# will be lost and the generated code won't follow it.
MARKER_INSTRUCTION = (
    "IMPORTANT: the script MUST include this exact line as valid Python, "
    "as the very first line of code: print(\"MARKER_TOKEN_7f3a9\")"
)

# Pad the task description with enough filler (simulating a long
# previous-failed-code + critic-reason block) to exceed the old
# ~4096 token default but stay under 32768.
FILLER = "\n".join([f"# filler context line {i}" for i in range(1500)])

task_description = f"""{MARKER_INSTRUCTION}

Then, write a script that computes the sum of the first 100 positive integers
and prints the result.

--- SIMULATED RETRY CONTEXT (previous failed attempt + critic reason) ---
{FILLER}
"""

def test_marker_survives_long_prompt():
    raw, cost = generate_code(task_description)
    print("--- PROMPT TOKENS ---")
    print(cost.get("prompt_tokens"))
    print("--- GENERATED CODE ---")
    print(raw)

    syntax = check_syntax(raw)
    assert syntax["valid"], f"Generated code is not valid Python: {syntax.get('error')}"

    assert 'print("MARKER_TOKEN_7f3a9")' in raw or "print('MARKER_TOKEN_7f3a9')" in raw, (
        "MARKER instruction from the START of task_description was not "
        "correctly incorporated as valid code -- possible front-truncation regression."
    )
    assert cost.get("prompt_tokens", 0) > 4096, (
        "Test prompt wasn't actually large enough to exercise the truncation-prone path."
    )
    print(f"PASS: marker instruction survived at {cost.get('prompt_tokens')} prompt tokens, num_ctx=32768 fix confirmed at Coder call site.")

if __name__ == "__main__":
    test_marker_survives_long_prompt()