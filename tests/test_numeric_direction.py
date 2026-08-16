import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.analyst.analyst_agent import check_numeric_direction

# Real reasoning strings from yesterday's B1 stress test (session 1, 5 runs).
cases = [
    ("correct run 1", "The adversarial model's accuracy under perturbation (0.89) is lower than that of the standard model (0.91), which refutes the hypothesis that adversarial training improves model robustness.", "consistent"),
    ("WRONG run 2 (known bug)", "The adversarial model shows a higher accuracy under perturbation (0.89) compared to the standard model (0.91), indicating that it is more robust.", "inconsistent"),
    ("correct run 3", "The adversarial model has a lower accuracy under perturbation (0.89) compared to the standard model (0.91), which refutes the hypothesis that adversarial training improves model robustness.", "consistent"),
    ("correct run 4", "The adversarial model shows a lower accuracy under perturbation (0.89) compared to the standard model (0.91), refuting the hypothesis that adversarial training improves model robustness.", "consistent"),
    ("correct run 5", "The adversarial model under perturbation shows a slightly lower accuracy (0.89) compared to the standard model (0.91), which suggests that it may not improve model robustness as expected.", "consistent"),
    ("self-contradictory run (2nd B1 batch)", "The adversarial model shows lower accuracy under perturbation (0.89) compared to standard training (0.91), indicating it performs better and is more robust against small perturbations.", "UNKNOWN — testing the stated limitation"),
    ("empty reasoning", "", "not checked"),
    ("no numbers, no direction words", "The model behaved as expected during training.", "not checked"),
    ("B2 cherry-pick (known blind spot)", "The new optimizer consistently reaches target loss in fewer steps than the baseline optimizer across all seeds.", "EXPECTED: NOT CHECKED (no numbers cited at all)"),
]

for label, reasoning, expected in cases:
    result = check_numeric_direction(reasoning)
    status = "consistent" if result.get("consistent") else ("inconsistent" if result["checked"] else "NOT CHECKED")
    match = "✓" if status == expected else "✗ MISMATCH"
    print(f"{label:30s} -> {status:15s} (expected {expected:12s}) {match}")
    if result.get("reason"):
        print(f"    reason: {result['reason']}")