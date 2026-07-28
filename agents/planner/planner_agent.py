import ollama
import json
from schemas.experiment_spec import ExperimentSpec

def plan_experiment(research_question:str,model:str="qwen2.5-coder:7b")->ExperimentSpec:
    schema=ExperimentSpec.model_json_schema()
    prompt = f"""You are a research planning agent. Given a research question,
produce a single, concrete, small-scale experiment that tests it.

The experiment must be small enough to run in under a minute on a single CPU,
with no GPU and no external datasets -- use synthetic/toy data if needed.

Research question:
{research_question}

Respond with ONLY a JSON object matching this schema, nothing else:
{json.dumps(schema, indent=2)}
"""
    response=ollama.generate(model=model,prompt=prompt)
    raw=response["response"].strip()
    start = raw.index("{")
    end = raw.rindex("}") + 1
    parsed = json.loads(raw[start:end])

    return ExperimentSpec(**parsed)

if __name__=="__main__":
    spec=plan_experiment(
        "Does using a smaller batch size lead to noisier but faster-converging training loss?"
    )
    print(spec.model_dump_json(indent=2))



