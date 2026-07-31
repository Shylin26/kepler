from neo4j import GraphDatabase

URI = "bolt://localhost:7687"
USER = "neo4j"
PASSWORD = "keplerpassword"

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

def run_write_query(query: str, parameters: dict = None) -> list:
    
    with driver.session() as session:
        result = session.run(query, parameters or {})
        return [record.data() for record in result]

def find_or_create_hypothesis(text: str, topic_area: str = "unspecified") -> str:
    """Return the existing Hypothesis's id if one with this exact text
    already exists; otherwise create a new one (tagged with its topic area)
    and return its id."""
    existing_id = find_hypothesis_by_text(text)
    if existing_id:
        return existing_id

    query = """
    CREATE (h:Hypothesis {text: $text, status: 'open', topic_area: $topic_area})
    RETURN elementId(h) AS id
    """
    result = run_write_query(query, {"text": text, "topic_area": topic_area})
    return result[0]["id"]

def log_run_to_graph(hypothesis_id: str, success: bool, attempts: int, trajectory_filepath: str) -> str:
    """Create a Run node, link it to an existing Hypothesis via TESTS, and
    return the Run node's internal id."""
    query = """
    MATCH (h:Hypothesis) WHERE elementId(h) = $hypothesis_id
    CREATE (r:Run {success: $success, attempts: $attempts, trajectory_file: $trajectory_filepath})
    CREATE (r)-[:TESTS]->(h)
    RETURN elementId(r) AS id
    """
    result = run_write_query(query, {
        "hypothesis_id": hypothesis_id,
        "success": success,
        "attempts": attempts,
        "trajectory_filepath": trajectory_filepath,
    })
    return result[0]["id"]

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

def get_covered_topic_areas() -> list[str]:
    """Return the distinct topic_area values already present in the graph."""
    query = """
    MATCH (h:Hypothesis)
    WHERE h.topic_area IS NOT NULL
    RETURN DISTINCT h.topic_area AS topic_area
    """
    results = run_write_query(query)
    return [r["topic_area"] for r in results]

if __name__ == "__main__":
    hyp_id = create_hypothesis("Using a smaller batch size leads to noisier but faster-converging training loss.")
    print(f"Created hypothesis with id: {hyp_id}")

    run_id = log_run_to_graph(
        hypothesis_id=hyp_id,
        success=True,
        attempts=2,
        trajectory_filepath="trajectories/20260729T142840Z.json",
    )
    print(f"Created run with id: {run_id}, linked to hypothesis {hyp_id}")