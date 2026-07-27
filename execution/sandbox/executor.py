import docker

def run_code_in_sandbox(code:str,timeout:int=30)->dict:
    client=docker.from_env()
    container=client.containers.run(
        image="python:3.11-slim",
        command=["python3", "-c", code],
        detach=True,
        network_disabled=True,
        mem_limit="512m",
        cpu_period=100000,
        cpu_quota=50000,
    )
    try:
        result=container.wait(timeout=timeout)
        exit_code=result["StatusCode"]
        logs=container.logs().decode("utf-8", errors="replace")
    except Exception as e:
        exit_code=-1
        logs = f"Container did not finish in time or errored: {e}"
        container.kill()
    finally:
        container.remove(force=True)
    return {"exit_code": exit_code, "output": logs}