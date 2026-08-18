import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.analyst.analyst_agent import check_generalization_scope


real_output = (
    "Seed 1: baseline=420 steps, new_optimizer=460 steps\n"
    "Seed 2: baseline=410 steps, new_optimizer=455 steps\n"
    "Seed 3: baseline=430 steps, new_optimizer=390 steps\n"
    "Seed 4: baseline=415 steps, new_optimizer=470 steps\n"
    "Seed 5: baseline=425 steps, new_optimizer=465 steps\n"
    "Mean: baseline=420.0 steps, new_optimizer=448.0 steps\n"
)

cases = [
    (
        "B2 cherry-pick (real bad run)",
        "The new optimizer consistently reaches target loss in fewer steps than the baseline optimizer across all seeds.",
        "Seed 3: baseline=430 steps, new_optimizer=390 steps",
        "SHOULD FLAG",
    ),
    (
        "B2 honest run (cites mean, no false universal claim)",
        "The new optimizer took more steps on average (448.0) compared to the baseline optimizer (420.0), which contradicts the hypothesis that it converges faster.",
        "Mean: baseline=420.0 steps, new_optimizer=448.0 steps",
        "should NOT flag (no universal language)",
    ),
    (
        "correctly-scoped universal claim (control -- should this false-positive?)",
        "The new optimizer consistently took more steps than the baseline across all 5 seeds and the mean.",
        "Mean: baseline=420.0 steps, new_optimizer=448.0 steps",
        "unclear -- testing whether it flags even a TRUE universal claim",
    ),
    ("empty reasoning, empty quote", "", "", "should not check"),
    ("universal language, no quote", "The optimizer consistently performs better across all seeds.", "", "should not check (no quote)"),

]

for label, reasoning, quote, expected in cases:
    result = check_generalization_scope(reasoning, quote, real_output)
    print(f"{label}")
    print(f"  expected: {expected}")
    print(f"  result: {result}")
    print()
