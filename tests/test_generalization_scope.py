import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.analyst.analyst_agent import check_generalization_scope

# The real multi-seed output from yesterday's B2 test.
real_output = (
    "Seed 1: baseline=420 steps, new_optimizer=460 steps\n"
    "Seed 2: baseline=410 steps, new_optimizer=455 steps\n"
    "Seed 3: baseline=430 steps, new_optimizer=390 steps\n"
    "Seed 4: baseline=415 steps, new_optimizer=470 steps\n"
    "Seed 5: baseline=425 steps, new_optimizer=465 steps\n"
    "Mean: baseline=420.0 steps, new_optimizer=448.0 steps\n"
)

epoch_output = (
    "Epoch 1: loss=0.82\n"
    "Epoch 2: loss=0.79\n"
    "Epoch 3: loss=0.61\n"
    "Epoch 4: loss=0.83\n"
    "Epoch 5: loss=0.80\n"
)

all_agree_output = (
    "Seed 1: baseline=420 steps, new_optimizer=380 steps\n"
    "Seed 2: baseline=410 steps, new_optimizer=375 steps\n"
    "Seed 3: baseline=430 steps, new_optimizer=390 steps\n"
    "Seed 4: baseline=415 steps, new_optimizer=385 steps\n"
    "Seed 5: baseline=425 steps, new_optimizer=395 steps\n"
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
    (
        "empty reasoning, empty quote",
        "",
        "",
        "should not check",
    ),
    (
        "universal language, no quote",
        "The optimizer consistently performs better across all seeds.",
        "",
        "should not check (no quote)",
    ),
    (
        "epoch cherry-pick (parallel to Seed-3 bug)",
        "Loss consistently decreased across all epochs, showing the model is learning well.",
        "Epoch 3: loss=0.61",
        "SHOULD FLAG",
    ),
    (
        "epoch honest run (no universal claim)",
        "Loss was inconsistent across epochs, dropping at epoch 3 but rising again afterward.",
        "Epoch 3: loss=0.61",
        "should NOT flag (no universal language)",
    ),
]

for label, reasoning, quote, expected in cases:
    output_to_use = epoch_output if "epoch" in label else real_output
    result = check_generalization_scope(reasoning, quote, output_to_use)
    print(f"{label}")
    print(f"  expected: {expected}")
    print(f"  result: {result}")
    print()

# New case: does a TRUE universal claim get flagged the same as a false one?
all_agree_reasoning = "The new optimizer consistently converges in fewer steps than the baseline across all seeds."
all_agree_quote = "Seed 3: baseline=430 steps, new_optimizer=390 steps"

all_agree_case = [
    (
        "TRUE universal claim, under-cited (does the flag distinguish this from a false one?)",
        all_agree_reasoning,
        all_agree_quote,
        "UNKNOWN -- expect it flags this too, same as the false case, since it can't verify truth",
    ),
]

for label, r, q, expected in all_agree_case:
    result = check_generalization_scope(r, q, all_agree_output)
    print(f"{label}")
    print(f"  expected: {expected}")
    print(f"  result: {result}")
    print()