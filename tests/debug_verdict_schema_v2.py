import json
from collections import Counter

import ollama
from agents.analyst.analyst_agent import analyze_result, check_grounding_multi

# (name, hypothesis, expected_outcome, output, truth)
# Truth labels are fixed BEFORE any run.
BATCH_H = "Doubling the batch size from 32 to 64 reduces final training loss by at least 10%."
BATCH_E = "Final loss with batch size 64 should be at least 10% lower than with batch size 32."
L2_H = "Adding L2 regularization reduces the magnitude of learned weights."
L2_E = "Weight magnitude with L2 should be smaller than without."

CASES = [
    ("batch64_better", BATCH_H, BATCH_E,
     "Batch size 32: final_loss=0.4213\nBatch size 64: final_loss=0.3510\n", "supports"),
    ("l2_shrinks", L2_H, L2_E,
     "No regularization: weight_norm=4.82\nL2 (lambda=0.1): weight_norm=2.31\n", "supports"),
    ("lr_diverges",
     "A learning rate of 1.01 diverges while 0.01 converges.",
     "Loss with lr=0.01 should decrease; loss with lr=1.01 should grow without bound.",
     "Learning Rate: 0.01\nStep 1, Loss: 0.9001\nStep 2, Loss: 0.4385\nStep 3, Loss: 0.2180\n"
     "Step 4, Loss: 0.0611\nStep 5, Loss: 0.0184\nLearning Rate: 1.01\nStep 1, Loss: 0.0128\n"
     "Step 2, Loss: 11.3\nStep 3, Loss: 9800.5\nStep 4, Loss: 8100000.2\nStep 5, Loss: 7.1e+09\n",
     "supports"),
    ("batch64_worse", BATCH_H, BATCH_E,
     "Batch size 32: final_loss=0.4213\nBatch size 64: final_loss=0.4599\n", "refutes"),
    ("l2_grows", L2_H, L2_E,
     "No regularization: weight_norm=2.10\nL2 (lambda=0.1): weight_norm=3.40\n", "refutes"),
    ("momentum_slower",
     "Adding momentum reduces the number of steps needed to reach loss < 0.1.",
     "The momentum run should need fewer steps than plain SGD.",
     "Plain SGD: 120 steps to reach loss < 0.1\nMomentum (0.9): 340 steps to reach loss < 0.1\n",
     "refutes"),
    ("irrelevant_output", L2_H, L2_E,
     "Epoch 1: loss=0.9\nEpoch 2: loss=0.5\n", "inconclusive"),
    ("missing_condition", BATCH_H, BATCH_E,
     "Batch size 32: final_loss=0.4213\n", "inconclusive"),
    ("no_numbers", L2_H, L2_E,
     "Training complete.\nDone.\n", "inconclusive"),
    # Most debatable label: per-seed results are mixed and the means are nearly equal.
    ("mixed_seeds",
     "Method B reaches the target loss in fewer steps than method A.",
     "B should need fewer steps than A.",
     "Seed 1: A=410 B=395\nSeed 2: A=388 B=402\nSeed 3: A=401 B=399\nSeed 4: A=395 B=397\n",
     "inconclusive"),
]

N = 5


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
        return "parse_error", False
    verdict = {"yes": "supports", "no": "refutes"}.get(
        str(d.get("matches_expected_outcome", "")).lower(), "inconclusive")
    if verdict != "inconclusive" and not check_grounding_multi(
            d.get("supporting_quotes") or [], output)["grounded"]:
        return "inconclusive", True  # same as production: failed grounding becomes inconclusive
    return verdict, False


tally = {}  # (arm, truth) -> [correct, total]
for name, hyp, exp, out, truth in CASES:
    row = {"OLD": [], "NEW": []}
    for _ in range(N):
        r = analyze_result(hyp, exp, out)
        row["OLD"].append(r["verdict"])
        row["NEW"].append(analyze_v2(hyp, exp, out)[0])
    for arm in ("OLD", "NEW"):
        c = tally.setdefault((arm, truth), [0, 0])
        c[0] += sum(v == truth for v in row[arm])
        c[1] += N
    print(f"{name} (truth={truth}): OLD={dict(Counter(row['OLD']))} NEW={dict(Counter(row['NEW']))}",
          flush=True)

print("\n=== ACCURACY BY TRUTH CLASS ===")
for arm in ("OLD", "NEW"):
    parts = [f"{t}: {tally[(arm, t)][0]}/{tally[(arm, t)][1]}"
             for t in ("supports", "refutes", "inconclusive")]
    tot_c = sum(tally[(arm, t)][0] for t in ("supports", "refutes", "inconclusive"))
    tot_n = sum(tally[(arm, t)][1] for t in ("supports", "refutes", "inconclusive"))
    print(f"{arm}: " + " | ".join(parts) + f" | overall {tot_c}/{tot_n}")