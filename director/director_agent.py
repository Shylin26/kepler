import ollama
import json
from memory.knowledge_graph.graph_client import run_write_query, get_covered_topic_areas
from memory.trajectory_store.llm_cost import extract_llm_cost

def get_existing_hypotheses() -> list[str]:
    """Return the text of every Hypothesis currently in the knowledge graph."""
    query = """
    MATCH (h:Hypothesis)
    RETURN h.text AS text
    """
    results = run_write_query(query)
    return [r["text"] for r in results]

def propose_topic_area(model: str = "qwen2.5-coder:7b") -> str:
    """Ask an LLM to propose a broad topic area to research next, distinct
    from areas already covered by existing hypotheses in the graph."""

    covered = get_covered_topic_areas()
    covered_list = "\n".join(f"- {t}" for t in covered) if covered else "(none yet)"

    prompt = f"""You are a research director for a small-scale ML experimentation system.
Your job right now is NOT to write a specific research question -- only to name
a broad TOPIC AREA to focus on next (e.g. "learning rate scheduling",
"weight initialization strategies", "optimizer choice", "regularization").

Topic areas must be small-scale-experiment-friendly: testable on a single CPU,
under a minute, with synthetic data, no third-party packages.

These EXACT topic areas have already been covered -- you MUST propose something
different from all of these:
{covered_list}

Respond with ONLY the topic area as a short phrase (3-6 words), nothing else.
No preamble, no explanation, no quotes.
"""

    response = ollama.generate(model=model, prompt=prompt)
    return response["response"].strip(), extract_llm_cost(response)

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
    return response["response"].strip(), extract_llm_cost(response)

if __name__ == "__main__":
    topic, topic_cost = propose_topic_area()
    print(f"=== PROPOSED TOPIC AREA: {topic} ===")
    print(f"--- LLM COST ---\n{topic_cost}")

    question, question_cost = propose_next_research_question(topic)
    print(f"=== PROPOSED RESEARCH QUESTION: {question} ===")
    print(f"--- LLM COST ---\n{question_cost}")