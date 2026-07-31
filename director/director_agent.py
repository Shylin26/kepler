import ollama
import json
from memory.knowledge_graph.graph_client import run_write_query

def get_existing_hypotheses() -> list[str]:
    """Return the text of every Hypothesis currently in the knowledge graph."""
    query = """
    MATCH (h:Hypothesis)
    RETURN h.text AS text
    """
    results = run_write_query(query)
    return [r["text"] for r in results]

def propose_next_research_question(topic_area: str, model: str = "qwen2.5-coder:7b") -> str:
    """Ask an LLM to propose a new research question in the given topic area,
    that hasn't already been explored according to the knowledge graph."""

    existing = get_existing_hypotheses()
    existing_list = "\n".join(f"- {h}" for h in existing) if existing else "(none yet)"

    prompt = f"""You are a research director for a small-scale ML experimentation system.
Propose ONE new, specific, testable research question in the topic area of: {topic_area}

The question must be answerable with a small-scale experiment (single CPU,
under a minute, synthetic data, no third-party packages).

Here are research questions that have ALREADY been explored -- do NOT propose
a question that is the same as, a rewording of, or a close variant of any of
these (e.g. flipping "smaller batch size" to "larger batch size" on the same
underlying comparison does NOT count as a new question):
{existing_list}

Respond with ONLY the new research question as a single sentence, nothing else.
No preamble, no explanation, no quotes around it.
"""

    response = ollama.generate(model=model, prompt=prompt)
    return response["response"].strip()

if __name__ == "__main__":
    question = propose_next_research_question("learning rate and convergence behavior")
    print("=== PROPOSED RESEARCH QUESTION ===")
    print(question)
