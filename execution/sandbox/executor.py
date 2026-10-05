import docker
import time

RUNAWAY_REPEAT_THRESHOLD = 15  # same line repeated this many times in a row = runaway
POLL_INTERVAL_SECONDS = 0.5

def _check_for_runaway(logs: str) -> dict:
    """Look at the tail of captured logs for a stuck loop: the same line
    repeating many times consecutively. Does NOT require nan/inf specifically
    -- any tight repeating print-loop wastes budget the same way -- but flags
    nan/inf separately since that's the originally observed failure mode."""
    lines = [l for l in logs.strip().split("\n") if l.strip()]
    if len(lines) < RUNAWAY_REPEAT_THRESHOLD:
        return {"runaway": False}

    tail = lines[-RUNAWAY_REPEAT_THRESHOLD:]
    if len(set(tail)) == 1:
        repeated_line = tail[0]
        is_nan_related = "nan" in repeated_line.lower() or "inf" in repeated_line.lower()
        return {
            "runaway": True,
            "repeated_line": repeated_line,
            "repeat_count_observed": RUNAWAY_REPEAT_THRESHOLD,
            "nan_related": is_nan_related,
        }
    return {"runaway": False}


def run_code_in_sandbox(code: str, timeout: int = 30) -> dict:
    client = docker.from_env()
    container = client.containers.run(
        image="python:3.11-slim",
        command=["python3", "-c", code],
        detach=True,
        network_disabled=True,
        mem_limit="512m",
        cpu_period=100000,
        cpu_quota=50000,
    )
    start = time.monotonic()
    exit_code = None
    logs = ""
    runaway_info = {"runaway": False}
    killed_early_for_runaway = False

    try:
        while True:
            elapsed = time.monotonic() - start
            container.reload()
            if container.status == "exited":
                result = container.wait(timeout=1)
                exit_code = result["StatusCode"]
                logs = container.logs().decode("utf-8", errors="replace")
                break

            if elapsed >= timeout:
                exit_code = -1
                logs = container.logs().decode("utf-8", errors="replace")
                logs += "\n[Container did not finish within timeout]"
                container.kill()
                break

            logs = container.logs().decode("utf-8", errors="replace")
            runaway_info = _check_for_runaway(logs)
            if runaway_info["runaway"]:
                exit_code = -2
                logs += "\n[Killed early: runaway output detected -- same line repeated " \
                        f"{runaway_info['repeat_count_observed']}+ times consecutively" \
                        f"{' (nan/inf related)' if runaway_info['nan_related'] else ''}]"
                container.kill()
                killed_early_for_runaway = True
                break

            time.sleep(POLL_INTERVAL_SECONDS)

    except Exception as e:
        exit_code = -1
        logs = f"Container did not finish in time or errored: {e}"
        container.kill()
    finally:
        duration_seconds = time.monotonic() - start
        container.remove(force=True)

    return {
        "exit_code": exit_code,
        "output": logs,
        "duration_seconds": round(duration_seconds, 3),
        "killed_early_for_runaway": killed_early_for_runaway,
        "runaway_info": runaway_info,
    }