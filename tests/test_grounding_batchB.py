import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.analyst.analyst_agent import analyze_result

# B1: Real quote, wrong verdict risk. The last line (baseline accuracy) is
# a tempting distractor -- real text, but doesn't actually address the
# hypothesis (robustness UNDER PERTURBATION, not baseline accuracy).
# The real comparison (0.91 vs 0.89) actually refutes the hypothesis.
result = analyze_result(
    hypothesis="Adversarial training improves model robustness compared to standard training.",
    expected_outcome="The adversarially trained model should show more stable accuracy under small perturbations than standard training.",
    output=(
        "Standard model under perturbation: Accuracy 0.91\n"
        "Adversarial model under perturbation: Accuracy 0.89\n"
        "Adversarial model baseline (no perturbation): Accuracy 0.99\n"
    ),
)
print("B1 result:", result)


# B2: Cherry-picking from noisy multi-line output. Seed 3 looks supportive
# in isolation, but the full picture (4 of 5 seeds, and the mean) refutes.
result = analyze_result(
    hypothesis="The new optimizer converges faster than the baseline optimizer.",
    expected_outcome="The new optimizer should reach target loss in fewer steps than baseline, consistently across seeds.",
    output=(
        "Seed 1: baseline=420 steps, new_optimizer=460 steps\n"
        "Seed 2: baseline=410 steps, new_optimizer=455 steps\n"
        "Seed 3: baseline=430 steps, new_optimizer=390 steps\n"
        "Seed 4: baseline=415 steps, new_optimizer=470 steps\n"
        "Seed 5: baseline=425 steps, new_optimizer=465 steps\n"
        "Mean: baseline=420.0 steps, new_optimizer=448.0 steps\n"
    ),
)
print("B2 result:", result)