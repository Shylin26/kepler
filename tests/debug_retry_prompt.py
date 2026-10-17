from agents.coder.coder_agent import generate_code, strip_markdown_fences

TASK = "Using only Python's standard library, simulate 100 epochs of training a tiny model that uses a sigmoid activation. Print the loss after each epoch."
BAD = '''import random

def sigmoid(x):
    return 1 / (1 + math.exp(-x))

random.seed(42)
w = random.random()
for epoch in range(100):
    p = sigmoid(w)
    loss = (p - 1) ** 2
    w += 0.1
    print(f"Epoch {epoch}: {loss:.4f}")
'''
ERR = "NameError: name 'math' is not defined"

OLD = f"""{TASK}
Your previous attempt failed. Here is the code you wrote:
{BAD}

Here is why it failed:
Non-zero exit code: 1. Output: Traceback (most recent call last): | {ERR}

Please fix the code and provide a corrected, complete script."""

NEW = f"""{TASK}
Your previous attempt FAILED with this exact error:
{ERR}

The code below is WRONG. Do not repeat it. Find the line that causes this error, change it, and make sure every name used is defined or imported.

Failing code:
{BAD}

Return the complete corrected script only."""

for label, prompt in (("OLD", OLD), ("NEW", NEW)):
    fixed = 0
    for i in range(5):
        raw, _ = generate_code(prompt)
        code = strip_markdown_fences(raw)
        ok = "import math" in code or "from math" in code
        fixed += ok
        print(f"{label} run {i+1}: fixed={ok}")
    print(f"=== {label}: {fixed}/5 fixed ===")