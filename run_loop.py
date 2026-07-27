from agents.coder.coder_agent import generate_code, strip_markdown_fences
from execution.sandbox.executor import run_code_in_sandbox
from agents.critic.critic_agent import basic_sanity_check, task_adherence_check

def run_with_self_correction(task_description: str, max_attempts: int = 3)->dict:
    task=task_description
    history=[]
    for attempt in range(1,max_attempts+1):
        print(f"\n=== Attempt {attempt} ===")

        raw=generate_code(task)
        code=strip_markdown_fences(raw)
        print("--- CODE ---")
        print(code)
        sandbox_result=run_code_in_sandbox(code)
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
    result = run_with_self_correction(
        "Write a script that computes the factorial of 15 using recursion, "
        "then divides 1000000 by (the factorial minus itself), and prints the result. "
        "Handle any errors gracefully by printing 'Error: <description>' instead of crashing."
    )
    print("\n=== FINAL RESULT ===")
    print(f"Success: {result['success']}, Attempts used: {result['attempts']}")