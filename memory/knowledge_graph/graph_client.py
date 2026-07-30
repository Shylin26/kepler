from neo4j import GraphDatabase

URI = "bolt://localhost:7687"
USER = "neo4j"
PASSWORD = "keplerpassword"

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

def run_write_query(query: str, parameters: dict = None) -> list:
    
    with driver.session() as session:
        result = session.run(query, parameters or {})
        return [record.data() for record in result]

if __name__ == "__main__":
    query = """
    CREATE (h:Hypothesis {text: $text, status: $status})
    RETURN h
    """
    result = run_write_query(query, {"text": "Test hypothesis from Python", "status": "open"})
    print(result)