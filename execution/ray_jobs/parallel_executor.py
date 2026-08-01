import ray 
import time
from execution.sandbox.executor import run_code_in_sandbox

@ray.remote

def run_code_in_sandbox_remote(code: str, timeout: int = 30) -> dict:
    """Ray-wrapped version of run_code_in_sandbox — runs as a Ray task
    instead of blocking the calling process."""
    start = time.time()
    result = run_code_in_sandbox(code, timeout=timeout)
    end = time.time()
    result["started_at"] = start
    result["finished_at"] = end
    return result

def run_many_in_parallel(code_snippets: list[str], timeout: int = 30) -> list[dict]:
    """Submit multiple code snippets to run in parallel sandboxes, and
    return all results once every job has finished."""
    if not ray.is_initialized():
        ray.init()

    futures = [run_code_in_sandbox_remote.remote(code, timeout) for code in code_snippets]
    results = ray.get(futures)
    return results


if __name__ == "__main__":
    import time

    snippets = [
        "print('job 1'); import time; time.sleep(3)",
        "print('job 2'); import time; time.sleep(3)",
        "print('job 3'); import time; time.sleep(3)",
    ]

    overall_start = time.time()
    results = run_many_in_parallel(snippets, timeout=10)
    elapsed = time.time() - overall_start

    for i, r in enumerate(results):
        rel_start = r["started_at"] - overall_start
        rel_end = r["finished_at"] - overall_start
        print(f"Job {i+1}: started at {rel_start:.2f}s, finished at {rel_end:.2f}s")

    print(f"\nTotal time: {elapsed:.2f} seconds")

    print("\n=== SECOND BATCH (Ray already warmed up) ===")
    overall_start_2 = time.time()
    results_2 = run_many_in_parallel(snippets, timeout=10)
    elapsed_2 = time.time() - overall_start_2

    for i, r in enumerate(results_2):
        rel_start = r["started_at"] - overall_start_2
        rel_end = r["finished_at"] - overall_start_2
        print(f"Job {i+1}: started at {rel_start:.2f}s, finished at {rel_end:.2f}s")

    print(f"\nTotal time (second batch): {elapsed_2:.2f} seconds")