from agents.coder.coder_agent import generate_code, strip_markdown_fences
from execution.sandbox.executor import run_code_in_sandbox
from agents.critic.critic_agent import basic_sanity_check, task_adherence_check
from memory.trajectory_store.logger import log_trajectory
from memory.knowledge_graph.graph_client import find_or_create_hypothesis, log_run_to_graph
from director.director_agent import propose_next_research_question, propose_topic_area


def run_with_self_correction(spec, max_attempts: int = 3)->dict:
    task_description = spec.task_description
    task = task_description
    history=[]
    for attempt in range(1,max_attempts+1):
        print(f"\n=== Attempt {attempt} ===")

        raw=generate_code(task)
        code=strip_markdown_fences(raw)
        print("--- CODE ---")
        print(code)
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




if __name__ == "__main__":
    from agents.planner.planner_agent import plan_experiment

    from director.director_agent import propose_topic_area
    topic_area = propose_topic_area()
    print(f"=== DIRECTOR PROPOSED TOPIC AREA: {topic_area} ===")

    research_question = propose_next_research_question(topic_area)
    print(f"=== DIRECTOR PROPOSED QUESTION: {research_question} ===")
    
    hypothesis_id = find_or_create_hypothesis(research_question, topic_area=topic_area)
    print(f"=== HYPOTHESIS CREATED IN GRAPH: {hypothesis_id} ===")

    print("=== PLANNING EXPERIMENT ===")
    spec = plan_experiment(research_question)
    print(spec.model_dump_json(indent=2))

    result = run_with_self_correction(spec)

    filepath = log_trajectory(research_question, spec, result)
    print(f"\n=== TRAJECTORY LOGGED TO: {filepath} ===")

    run_id = log_run_to_graph(
        hypothesis_id=hypothesis_id,
        success=result["success"],
        attempts=result["attempts"],
        trajectory_filepath=filepath,
    )
    print(f"=== RUN LOGGED TO GRAPH: {run_id} (linked to hypothesis {hypothesis_id}) ===")

    print("\n=== FINAL RESULT ===")
    print(f"Success: {result['success']}, Attempts used: {result['attempts']}")