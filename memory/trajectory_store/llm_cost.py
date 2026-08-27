def extract_llm_cost(response) -> dict:
    """Extract cost/timing metadata from a raw ollama.generate() response.

    Ollama's raw duration fields are nanoseconds -- converted to seconds
    here for consistency with total_sandbox_seconds elsewhere in the
    codebase. load_duration is the ONE-TIME cost of loading the model
    into memory (large on a cold start, ~0 once the model is already
    warm) -- reported separately from inference_duration so a single
    cold-start call doesn't make later warm calls look artificially
    expensive/cheap by comparison, and so cost analysis isn't skewed by
    one-time loading cost.

    Returns zeros (not a crash) if the response is missing expected
    fields -- defensive against a malformed or unexpected response shape.
    """
    try:
        total_ns = response["total_duration"] or 0
        load_ns = response["load_duration"] or 0
        prompt_tokens = response["prompt_eval_count"] or 0
        completion_tokens = response["eval_count"] or 0
    except (KeyError, TypeError):
        return {
            "total_duration_seconds": 0.0,
            "load_duration_seconds": 0.0,
            "inference_duration_seconds": 0.0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }
    return {
        "total_duration_seconds": round(total_ns / 1e9, 3),
        "load_duration_seconds": round(load_ns / 1e9, 3),
        "inference_duration_seconds": round((total_ns - load_ns) / 1e9, 3),
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
    }