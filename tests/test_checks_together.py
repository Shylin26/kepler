import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.analyst.analyst_agent import check_numeric_direction, check_generalization_scope

output = (
    "Seed 1: baseline=420 steps, new_optimizer=460 steps\n"
    "Seed 2: baseline=410 steps, new_optimizer=455 steps\n"
    "Seed 3: baseline=430 steps, new_optimizer=390 steps\n"
    "Seed 4: baseline=415 steps, new_optimizer=470 steps\n"
    "Seed 5: baseline=425 steps, new_optimizer=465 steps\n"
)
reasoning = "The new optimizer consistently shows higher step counts (390) compared to baseline (430) across all seeds, proving it converges faster."
quote = "Seed 3: baseline=430 steps, new_optimizer=390 steps"

direction_result = check_numeric_direction(reasoning)
generalization_result = check_generalization_scope(reasoning, quote, output)

print("direction_check:", direction_result)
print("generalization_check:", generalization_result)