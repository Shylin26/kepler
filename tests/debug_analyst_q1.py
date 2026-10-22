import re
import subprocess
import sys
import tempfile

from agents.analyst.analyst_agent import analyze_result

SCRIPT = '''
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

HYP = ("Using an extremely high learning rate causes SGD to diverge rather than "
       "converge when training a simple linear regression model on synthetic data.")
EXP = ("The run with the extremely high learning rate should diverge, while the "
       "well-tuned run should decrease toward a minimum.")


def clamp_big_numbers(text: str) -> str:
    return re.sub(r"\d{100,}(?:\.\d+)?", ">1e100", text)


with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
    f.write(SCRIPT)
raw_out = subprocess.run([sys.executable, f.name], capture_output=True, text=True).stdout
clamped_out = clamp_big_numbers(raw_out)
print("raw chars:", len(raw_out), "| clamped chars:", len(clamped_out))

import agents.analyst.analyst_agent as aa
real_cap = aa.cap_output

arms = (("RAW_UNCAPPED", raw_out, lambda s: s),
        ("CLAMPED", clamped_out, real_cap))
for label, out, capfn in arms:
    aa.cap_output = capfn
    counts = {"supports": 0, "refutes": 0, "inconclusive": 0}
    downgraded = 0
    for i in range(10):
        r = analyze_result(HYP, EXP, out)
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
        downgraded += r["reasoning"].startswith("[DOWNGRADED")
        print(f"{label} run {i+1}: {r['verdict']}")
        if i < 3:
            print("   REASONING:", r["reasoning"][:300].replace("\n", " "))
            print("   QUOTES:", str(r.get("supporting_quotes", r.get("rejected_quotes")))[:200])
    print(f"=== {label}: {counts} | downgraded: {downgraded}/10 ===")
aa.cap_output = real_cap