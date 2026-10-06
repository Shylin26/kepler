"""
Test for semantic hypothesis dedup in memory/knowledge_graph/graph_client.py.
Confirms: (1) an exact-text duplicate is still caught via the fast-path,
(2) a semantically similar but differently-worded hypothesis IS caught as
a duplicate (the actual new capability), (3) a genuinely different
hypothesis is NOT falsely flagged as a duplicate.

Uses real Neo4j (requires kepler-neo4j running) and real embeddings (no
mocking) -- this is testing the real decision boundary, not a stub.

Hypothesis text is tagged with a unique run_tag per test run to avoid
colliding with leftover data from earlier debugging sessions in the graph
(a real collision was caught during development -- see NOTES.md).
"""

import uuid
from memory.knowledge_graph.graph_client import find_or_create_hypothesis, run_write_query

def _cleanup(topic_area):
    """Remove test hypotheses so repeated runs don't pollute the graph."""
    run_write_query(
        "MATCH (h:Hypothesis {topic_area: $topic_area}) DETACH DELETE h",
        {"topic_area": topic_area},
    )

def test_semantic_dedup():
    topic_area = f"test_semantic_dedup_{uuid.uuid4().hex[:8]}"
    try:
        run_tag = uuid.uuid4().hex[:6]
        original = f"Does using a smaller batch size lead to noisier but faster-converging training loss? [{run_tag}]"
        reworded = f"How does mini-batch sizing impact how fast training converges? [{run_tag}]"
        different = f"Does L1 regularization improve generalization compared to L2? [{run_tag}]"

        id1 = find_or_create_hypothesis(original, topic_area=topic_area)
        print(f"Created original: {id1}")

        id2 = find_or_create_hypothesis(original, topic_area=topic_area)
        assert id2 == id1, "Exact-text duplicate was NOT caught -- regression in existing fast-path."
        print("PASS: exact-text duplicate correctly matched.")

        id3 = find_or_create_hypothesis(reworded, topic_area=topic_area)
        assert id3 == id1, (
            f"Reworded, semantically-equivalent hypothesis was NOT matched as a duplicate "
            f"(got new id {id3} instead of {id1}) -- semantic dedup failed."
        )
        print("PASS: reworded, semantically-equivalent hypothesis correctly matched as duplicate.")

        id4 = find_or_create_hypothesis(different, topic_area=topic_area)
        assert id4 != id1, (
            "Genuinely different hypothesis was INCORRECTLY matched as a duplicate -- "
            "threshold may be too low."
        )
        print("PASS: genuinely different hypothesis correctly NOT matched.")

        print("\nAll semantic dedup tests passed.")
    finally:
        _cleanup(topic_area)
        print(f"Cleaned up test data (topic_area={topic_area}).")

if __name__ == "__main__":
    test_semantic_dedup()