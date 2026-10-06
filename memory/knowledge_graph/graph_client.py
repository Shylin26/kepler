from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim

URI = "bolt://localhost:7687"
USER = "neo4j"
PASSWORD = "keplerpassword"

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

def run_write_query(query: str, parameters: dict = None) -> list:

    with driver.session() as session:
        result = session.run(query, parameters or {})
        return [record.data() for record in result]

_embedding_model = None

def _get_embedding_model():
    """Load the sentence-embedding model once and reuse it -- loading takes
    ~15-20s, far too slow to repeat per call."""
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedding_model

def get_embedding(text: str) -> list[float]:
    model = _get_embedding_model()
    return model.encode(text).tolist()

SIMILARITY_THRESHOLD = 0.75  # judgment call, not empirically tuned against
                              # a broad real dataset yet -- see NOTES.md

def find_hypothesis_by_text(text: str) -> str | None:
    """Return the elementId of an existing Hypothesis with this exact text,
    or None if no match exists."""
    query = """
    MATCH (h:Hypothesis {text: $text})
    RETURN elementId(h) AS id
    LIMIT 1
    """
    result = run_write_query(query, {"text": text})
    if result:
        return result[0]["id"]
    return None

def find_similar_hypothesis(text: str) -> dict | None:
    """Return info about an existing Hypothesis that's either an exact
    text match, or semantically similar above SIMILARITY_THRESHOLD.
    Returns None if nothing matches closely enough.

    Note: only Hypothesis nodes that have a stored embedding are considered
    for semantic matching -- nodes created before this feature was added
    won't have one, and are silently skipped (not an error, but a real
    scope limitation: they're invisible to semantic dedup until backfilled)."""
    exact_id = find_hypothesis_by_text(text)
    if exact_id:
        return {"id": exact_id, "match_type": "exact", "similarity": 1.0}

    query = """
    MATCH (h:Hypothesis)
    WHERE h.embedding IS NOT NULL
    RETURN elementId(h) AS id, h.text AS text, h.embedding AS embedding
    """
    existing = run_write_query(query)
    if not existing:
        return None

    new_embedding = get_embedding(text)
    best_match = None
    best_score = 0.0
    for row in existing:
        score = cos_sim(new_embedding, row["embedding"]).item()
        if score > best_score:
            best_score = score
            best_match = row

    if best_match and best_score >= SIMILARITY_THRESHOLD:
        return {
            "id": best_match["id"],
            "match_type": "semantic",
            "similarity": round(best_score, 4),
            "matched_text": best_match["text"],
        }
    return None

def find_or_create_hypothesis(text: str, topic_area: str = "unspecified") -> str:
    """Return the existing Hypothesis's id if one with this exact text or
    a semantically similar one already exists; otherwise create a new one
    (tagged with its topic area and embedding) and return its id."""
    match = find_similar_hypothesis(text)
    if match:
        if match["match_type"] == "semantic":
            print(f"--- SEMANTIC DEDUP: new hypothesis matched existing one "
                  f"(similarity={match['similarity']}): '{match['matched_text']}' ---")
        return match["id"]

    embedding = get_embedding(text)
    query = """
    CREATE (h:Hypothesis {text: $text, status: 'open', topic_area: $topic_area, embedding: $embedding})
    RETURN elementId(h) AS id
    """
    result = run_write_query(query, {"text": text, "topic_area": topic_area, "embedding": embedding})
    return result[0]["id"]

def get_covered_topic_areas() -> list[str]:
    """Return the distinct topic_area values already present in the graph."""
    query = """
    MATCH (h:Hypothesis)
    RETURN DISTINCT h.topic_area AS topic_area
    """
    result = run_write_query(query)
    return [r["topic_area"] for r in result if r["topic_area"]]

def get_existing_hypotheses() -> list[str]:
    """Return the text of every Hypothesis currently in the knowledge graph."""
    query = """
    MATCH (h:Hypothesis)
    RETURN h.text AS text
    """
    results = run_write_query(query)
    return [r["text"] for r in results]

def log_run_to_graph(hypothesis_id: str, success: bool, attempts: int, trajectory_filepath: str, total_sandbox_seconds: float = 0.0, budget_exceeded: bool = False) -> str:
    query = """
    MATCH (h:Hypothesis) WHERE elementId(h) = $hypothesis_id
    CREATE (r:Run {success: $success, attempts: $attempts, trajectory_file: $trajectory_filepath, total_sandbox_seconds: $total_sandbox_seconds, budget_exceeded: $budget_exceeded})
    CREATE (r)-[:TESTS]->(h)
    RETURN elementId(r) AS id
    """
    result = run_write_query(query, {
        "hypothesis_id": hypothesis_id,
        "success": success,
        "attempts": attempts,
        "trajectory_filepath": trajectory_filepath,
        "total_sandbox_seconds": total_sandbox_seconds,
        "budget_exceeded": budget_exceeded,
    })
    return result[0]["id"]