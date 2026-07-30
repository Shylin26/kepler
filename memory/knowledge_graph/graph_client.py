from neo4j import GraphDatabase

URI = "bolt://localhost:7687"
USER = "neo4j"
PASSWORD = "keplerpassword"

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

def run_write_query(query: str, parameters: dict = None) -> list:
    
    with driver.session() as session:
        result = session.run(query, parameters or {})
        return [record.data() for record in result]

def create_hypothesis(text: str) -> str:
    """Create a Hypothesis node and return its internal Neo4j id."""
    query = """
    CREATE (h:Hypothesis {text: $text, status: 'open'})
    RETURN elementId(h) AS id
    """
    result = run_write_query(query, {"text": text})
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