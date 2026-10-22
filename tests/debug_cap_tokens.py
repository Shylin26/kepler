import random
from agents.critic.critic_agent import task_adherence_check

random.seed(0)
out = "".join(
    f"Step {i}, Loss: " + "".join(random.choice("0123456789") for _ in range(240)) + "\n"
    for i in range(170)
)
print("output chars:", len(out))
r = task_adherence_check("Simulate gradient descent and print the loss each step.", "print(1)", out)
print("critic prompt_tokens:", r["llm_cost"]["prompt_tokens"])