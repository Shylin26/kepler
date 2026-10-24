from unittest.mock import patch
import agents.coder.coder_agent as cg

def test_prompt_has_output_rule_and_keeps_task():
    cap = {}
    def gen(**kw):
        cap["prompt"] = kw["prompt"]
        return {"response": "print(1)", "total_duration": 1, "load_duration": 0,
                "prompt_eval_count": 1, "eval_count": 1}
    with patch.object(cg.ollama, "generate", side_effect=gen):
        cg.generate_code("TASK_MARKER do the thing")
    assert "TASK_MARKER" in cap["prompt"]
    assert "OUTPUT SIZE" in cap["prompt"]
    assert "1e100" in cap["prompt"]

if __name__ == "__main__":
    test_prompt_has_output_rule_and_keeps_task()
    print("coder prompt output-rule test passed")