import ollama
import json
from schemas.experiment_spec import ExperimentSpec

def plan_experiment(research_question:str,model:str="qwen2.5-coder:7b")->ExperimentSpec:
    example = ExperimentSpec(
        hypothesis="A higher learning rate causes training loss to oscillate instead of decreasing smoothly.",
        task_description="Using only Python's standard library, simulate 20 steps of gradient "
                          "descent on a simple quadratic function once with a small learning rate "
                          "and once with a large learning rate. Print the value at each step for both.",
        expected_outcome="The large learning rate run should show the value oscillating or "
                          "diverging, while the small learning rate run should decrease smoothly.",
        success_criteria="The script runs to completion and prints 20 numeric values for each "
                          "learning rate setting.",
        compute_budget_seconds=60,
        notes=None,
    )

    prompt = f"""You are a research planning agent. Given a research question,
produce a single, concrete, small-scale experiment that tests it.

The experiment must be small enough to run in under a minute on a single CPU,
with no GPU and no external datasets -- use synthetic/toy data if needed.

CRITICAL CONSTRAINT: the code will run in a bare Python 3.11 sandbox with NO
extra packages installed -- only the Python standard library is available.
Do NOT use numpy, pandas, matplotlib, torch, or any other third-party package.
Implement any needed math (e.g. random data generation, basic arithmetic)
using only built-in Python (the `random`, `math`, and `statistics` modules
are fine). Represent any "plots" as printed text summaries (e.g. printed
loss values per epoch) instead of actual graphical plots.

Research question:
{research_question}

Here is an EXAMPLE of a well-formed response for a different research question,
showing the exact JSON structure to follow:
{example.model_dump_json(indent=2)}

Now produce your own JSON object, with the SAME fields, filled in with real
content for the research question above -- not the example's content.
Respond with ONLY the JSON object, nothing else.
"""
    response = ollama.generate(model=model, prompt=prompt)
    raw = response["response"].strip()
    start = raw.index("{")
    end = raw.rindex("}") + 1
    parsed = json.loads(raw[start:end])

    return ExperimentSpec(**parsed)

if __name__=="__main__":
    spec=plan_experiment(
        "Does using a smaller batch size lead to noisier but faster-converging training loss?"
    )
    print(spec.model_dump_json(indent=2))



