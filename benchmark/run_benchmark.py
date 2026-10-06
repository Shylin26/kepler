"""
Milestone 4 benchmark runner. Runs each PlantedQuestion through the real
pipeline (Director skipped -- the question is already fixed), captures
results, and scores them.

Scoring split, deliberately:
- coder_sandbox_valid and verdict_match are MECHANICAL -- derived directly
  from run_with_self_correction()'s success flag and Analyst's verdict vs.
  ground truth. No judgment call, just facts.
- planner_sound and critic_correct are left for HUMAN review (printed in
  full, not auto-scored) -- at this small scale (5 questions), a human
  read is more trustworthy than introducing an LLM-judged scoring step,
  given Critic's own documented inconsistency (issue #1) makes "judge
  quality via LLM" a known risk we're deliberately not taking on here.
"""

import json
from datetime import datetime, timezone
from benchmark.planted_questions import PLANTED_QUESTIONS
from agents.planner.planner_agent import plan_experiment
from run_loop import run_with_self_correction
from agents.analyst.analyst_agent import analyze_result


def run_benchmark():
    results = []

    for pq in PLANTED_QUESTIONS:
        print(f"\n{'='*70}")
        print(f"=== PLANTED QUESTION: {pq.id} ({pq.mechanism}) ===")
        print(f"{'='*70}")
        print(f"Research question: {pq.research_question}")
        print(f"Ground truth: {pq.ground_truth_verdict}")

        spec, planner_cost = plan_experiment(pq.research_question)
        print(f"\n--- PLANNER OUTPUT ---")
        print(f"Hypothesis: {spec.hypothesis}")
        print(f"Task description: {spec.task_description}")
        print(f"Expected outcome: {spec.expected_outcome}")

        loop_result = run_with_self_correction(spec, max_attempts=3)
        coder_sandbox_valid = loop_result["success"]
        print(f"\n--- CODER/SANDBOX RESULT ---")
        print(f"Success: {coder_sandbox_valid}, Attempts: {loop_result['attempts']}")

        analysis = None
        verdict_match = None
        if coder_sandbox_valid:
            last_attempt = loop_result["history"][-1]
            output = last_attempt["sandbox_result"].get("output", "")
            analysis = analyze_result(spec.hypothesis, spec.expected_outcome, output)
            print(f"\n--- ANALYST VERDICT ---")
            print(f"Verdict: {analysis['verdict']}")
            print(f"Reasoning: {analysis['reasoning']}")
            verdict_match = (analysis["verdict"] == pq.ground_truth_verdict)
            print(f"Ground truth match: {verdict_match}")
        else:
            print("\n--- ANALYST SKIPPED (Coder/sandbox did not succeed) ---")

        print(f"\n--- CRITIC REASONING (for human review) ---")
        for i, attempt in enumerate(loop_result["history"]):
            print(f"  Attempt {i+1}: {attempt['verdict'].get('reason', 'N/A')[:300]}")

        results.append({
            "id": pq.id,
            "mechanism": pq.mechanism,
            "ground_truth_verdict": pq.ground_truth_verdict,
            "planner_task_description": spec.task_description,
            "planner_hypothesis": spec.hypothesis,
            "coder_sandbox_valid": coder_sandbox_valid,
            "attempts": loop_result["attempts"],
            "analyst_verdict": analysis["verdict"] if analysis else None,
            "analyst_reasoning": analysis["reasoning"] if analysis else None,
            "verdict_match": verdict_match,
            "critic_history": [
                {"attempt": i + 1, "reason": a["verdict"].get("reason", "")}
                for i, a in enumerate(loop_result["history"])
            ],
            # Left blank intentionally -- for human scoring after the run
            "planner_sound_human_judgment": None,
            "critic_correct_human_judgment": None,
        })

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    filepath = f"benchmark/results_{timestamp}.json"
    with open(filepath, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n\n{'='*70}")
    print("=== BENCHMARK SUMMARY ===")
    print(f"{'='*70}")
    for r in results:
        match_str = "N/A (sandbox failed)" if r["verdict_match"] is None else r["verdict_match"]
        print(f"{r['id']} ({r['mechanism']}): coder_sandbox_valid={r['coder_sandbox_valid']}, "
              f"verdict={r['analyst_verdict']}, ground_truth={r['ground_truth_verdict']}, "
              f"match={match_str}")
    print(f"\nFull results saved to {filepath}")
    print("NEXT STEP: manually review planner_task_description and critic_history for "
          "each question, fill in planner_sound_human_judgment and "
          "critic_correct_human_judgment in the saved JSON.")

    return results


if __name__ == "__main__":
    run_benchmark()