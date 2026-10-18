import json
from unittest.mock import patch
import agents.critic.critic_agent as ca
import agents.analyst.analyst_agent as aa

BIG = "OUTPUT_START\n" + ("x" * 60000) + "\nOUTPUT_END"

def _fake(payload, captured):
    def gen(**kw):
        captured["prompt"] = kw["prompt"]
        return {"response": json.dumps(payload), "total_duration": 1,
                "load_duration": 0, "prompt_eval_count": 1, "eval_count": 1}
    return gen

def test_critic_prompt_is_capped_and_keeps_task():
    cap = {}
    with patch.object(ca.ollama, "generate",
                      side_effect=_fake({"adheres_to_task": True, "reason": "ok"}, cap)):
        ca.task_adherence_check("TASK_MARKER do the thing", "print(1)", BIG)
    assert "TASK_MARKER" in cap["prompt"]
    assert "characters omitted" in cap["prompt"]
    assert len(cap["prompt"]) < 20000

def test_analyst_prompt_is_capped_and_keeps_hypothesis():
    cap = {}
    with patch.object(aa.ollama, "generate",
                      side_effect=_fake({"verdict": "inconclusive", "reasoning": "r",
                                         "supporting_quotes": []}, cap)):
        aa.analyze_result("HYPOTHESIS_MARKER", "expected", BIG)
    assert "HYPOTHESIS_MARKER" in cap["prompt"]
    assert "characters omitted" in cap["prompt"]
    assert len(cap["prompt"]) < 20000

if __name__ == "__main__":
    test_critic_prompt_is_capped_and_keeps_task()
    test_analyst_prompt_is_capped_and_keeps_hypothesis()
    print("prompt cap tests passed")