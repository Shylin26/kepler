import json
import os
from datetime import datetime,timezone

def log_trajectory(research_question: str, spec, loop_result: dict) -> str:
    os.makedirs("trajectories", exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    filename = f"trajectories/{timestamp}.json"
    record = {
        "timestamp_utc": timestamp,
        "research_question": research_question,
        "experiment_spec": spec.model_dump(),
        "success": loop_result["success"],
        "attempts_used": loop_result["attempts"],
        "final_code": loop_result["final_code"],
        "history": loop_result["history"],
    }
    with open(filename, "w") as f:
        json.dump(record, f, indent=2)

    return filename


