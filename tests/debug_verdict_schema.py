import json
import subprocess
import sys
import tempfile
from collections import Counter

import ollama
import agents.analyst.analyst_agent as aa
from agents.analyst.analyst_agent import analyze_result, check_grounding_multi

aa.cap_output = lambda s: s  

Q1_SCRIPT = '''
import random
random.seed(42)
n_samples = 100
X = [[random.uniform(-1, 1), random.uniform(-1, 1)] for _ in range(n_samples)]
y = [x[0] + x[1] + random.gauss(0, 0.1) for x in X]
theta = [random.gauss(0, 1), random.gauss(0, 1)]
for lr in [0.01, 101 * 0.01]:
    print(f"Learning Rate: {lr}")
    theta_temp = theta.copy()
    for step in range(100):
        gradients = [0, 0]
        for i in range(n_samples):
            prediction = theta[0] * X[i][0] + theta[1] * X[i][1]
            error = prediction - y[i]
            gradients[0] += error * X[i][0]
            gradients[1] += error * X[i][1]
        for j in range(2):
            theta_temp[j] -= lr * gradients[j]
        loss = sum((theta[0] * x[0] + theta[1] * x[1] - yy) ** 2 for x, yy in zip(X, y)) / n_samples
        print(f"Step {step+1}, Loss: {loss:.4f}")
        if abs(theta_temp[j] - theta[j]) < 1e-6:
            break
        theta = theta_temp.copy()
'''


def run_q1():
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(Q1_SCRIPT)
    return subprocess.run([sys.executable, f.name], capture_output=True, text=True).stdout


def analyze_v2(hyp, exp, output):
    prompt = f"""You are a careful research analyst.

Hypothesis:
{hyp}

Expected outcome if the hypothesis is true:
{exp}

Actual experiment output:
{output}

Step 1: State in one sentence what the output actually shows.
Step 2: Does the actual output MATCH the expected outcome? Answer "yes" if it matches, "no" if it clearly contradicts it, "unclear" if the output does not contain enough information.

Support your answer with DIRECT QUOTES copied exactly from the output. Each quote must be one contiguous piece of the output.

Respond with ONLY JSON: {{"observed": "one sentence", "matches_expected_outcome": "yes" or "no" or "unclear", "supporting_quotes": ["exact substring"]}}
"""
    resp = ollama.generate(model="qwen2.5-coder:7b", prompt=prompt, options={"num_ctx": 32768})
    raw = resp["response"].strip()
    try:
        d = json.loads(raw[raw.index("{"): raw.rindex("}") + 1])
    except Exception:
        return "parse_error"
    verdict = {"yes": "supports", "no": "refutes"}.get(str(d.get("matches_expected_outcome", "")).lower(), "inconclusive")
    if verdict != "inconclusive" and not check_grounding_multi(d.get("supporting_quotes") or [], output)["grounded"]:
        return "downgraded"
    return verdict


CASES = [
    ("q1_diverges", "Using an extremely high learning rate causes SGD to diverge rather than converge when training a simple linear regression model on synthetic data.",
     "The run with the extremely high learning rate should diverge, while the well-tuned run should decrease toward a minimum.", run_q1(), "supports"),
    ("batch_loss_worse", "Doubling the batch size from 32 to 64 reduces final training loss by at least 10%.",
     "Final loss with batch size 64 should be at least 10% lower than with batch size 32.",
     "Batch size 32: final_loss=0.4213 | Batch size 64: final_loss=0.4599", "refutes"),
    ("irrelevant_output", "Adding L2 regularization reduces the magnitude of learned weights.",
     "Weight magnitudes with L2 should be smaller than without.", "Epoch 1: loss=0.9\nEpoch 2: loss=0.5\n", "inconclusive"),
]

N = 6
first = True
for name, hyp, exp, out, truth in CASES:
    old, new = [], []
    for _ in range(N):
        r = analyze_result(hyp, exp, out)
        if first:
            print("Q1 uncapped:", len(out), "chars,", r["llm_cost"]["prompt_tokens"], "prompt tokens")
            first = False
        old.append(r["verdict"])
        new.append(analyze_v2(hyp, exp, out))
    print(f"{name} (truth={truth}): OLD={dict(Counter(old))} NEW={dict(Counter(new))}")