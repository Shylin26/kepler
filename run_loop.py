import ray
from agents.coder.coder_agent import generate_code, strip_markdown_fences
from execution.sandbox.executor import run_code_in_sandbox
from agents.critic.critic_agent import basic_sanity_check, task_adherence_check
from memory.trajectory_store.logger import log_trajectory
from memory.knowledge_graph.graph_client import find_or_create_hypothesis, log_run_to_graph
from director.director_agent import propose_next_research_question, propose_topic_area
from agents.coder.coder_agent import generate_code, strip_markdown_fences, check_syntax


def run_with_self_correction(spec, max_attempts: int = 3)->dict:
    task_description = spec.task_description
    task = task_description
    history=[]
    for attempt in range(1,max_attempts+1):
        print(f"\n=== Attempt {attempt} ===")

        raw = generate_code(task)
        code = strip_markdown_fences(raw)
        print("--- CODE ---")
        print(code)

        syntax_check = check_syntax(code)
        if not syntax_check["valid"]:
            print("--- SYNTAX CHECK FAILED (skipped sandbox run) ---")
            print(syntax_check["error"])
            sandbox_result = {"exit_code": 1, "output": syntax_check["error"]}
        else:
            sandbox_result = run_code_in_sandbox(code, timeout=spec.compute_budget_seconds)
        sandbox_result = run_code_in_sandbox(code, timeout=spec.compute_budget_seconds)
        print("--- SANDBOX RESULT ---")
        print(sandbox_result)
        verdict = basic_sanity_check(sandbox_result)
        if verdict["passed"]:
            verdict = task_adherence_check(
                task_description=task_description,
                code=code,
                output=sandbox_result.get("output", ""),
            )
        print("--- CRITIC VERDICT ---")
        print(verdict)
        history.append({
            "attempt": attempt,
            "code": code,
            "sandbox_result": sandbox_result,
            "verdict": verdict,

        })
        if verdict["passed"]:
            return {"success": True, "final_code": code, "attempts": attempt, "history": history}

        task = f"""{task_description}
Your previous attempt failed. Here is the code you wrote:
{code}

Here is why it failed:
{verdict['reason']}

Please fix the code and provide a corrected, complete script."""

    return {"success": False, "final_code": code, "attempts": max_attempts, "history": history}

@ray.remote
def run_with_self_correction_remote(spec, max_attempts: int = 3) -> dict:
    """Ray-wrapped version of run_with_self_correction — runs the full
    Planner-output-to-Critic-verdict loop as an independent Ray task."""
    return run_with_self_correction(spec, max_attempts=max_attempts)

def run_multiple_experiments(specs: list, hypothesis_id: str, research_question: str, max_attempts: int = 3) -> list:
    """Run multiple ExperimentSpecs in parallel via Ray, logging each result
    to the trajectory store and knowledge graph as it completes."""
    if not ray.is_initialized():
        ray.init()

    futures = [run_with_self_correction_remote.remote(spec, max_attempts) for spec in specs]
    results = ray.get(futures)

    logged_results = []
    for spec, result in zip(specs, results):
        filepath = log_trajectory(research_question, spec, result)
        run_id = log_run_to_graph(
            hypothesis_id=hypothesis_id,
            success=result["success"],
            attempts=result["attempts"],
            trajectory_filepath=filepath,
        )
        logged_results.append({"spec": spec, "result": result, "run_id": run_id, "filepath": filepath})

    return logged_results


if __name__ == "__main__":
    from agents.planner.planner_agent import plan_experiment

    from director.director_agent import propose_topic_area
    topic_area = propose_topic_area()
    print(f"=== DIRECTOR PROPOSED TOPIC AREA: {topic_area} ===")

    research_question = propose_next_research_question(topic_area)
    print(f"=== DIRECTOR PROPOSED QUESTION: {research_question} ===")
    
    hypothesis_id = find_or_create_hypothesis(research_question, topic_area=topic_area)
    print(f"=== HYPOTHESIS CREATED IN GRAPH: {hypothesis_id} ===")

    num_variations = 3
    print(f"=== PLANNING {num_variations} EXPERIMENT VARIATIONS ===")
    specs = [plan_experiment(research_question) for _ in range(num_variations)]
    for i, s in enumerate(specs):
        print(f"--- Variation {i+1} task: {s.task_description}")

    print(f"\n=== RUNNING {num_variations} EXPERIMENTS IN PARALLEL ===")
    logged_results = run_multiple_experiments(specs, hypothesis_id, research_question)

    print("\n=== FINAL RESULTS ===")
    for i, lr in enumerate(logged_results):
        print(f"Variation {i+1}: Success={lr['result']['success']}, Attempts={lr['result']['attempts']}, Run ID={lr['run_id']}")