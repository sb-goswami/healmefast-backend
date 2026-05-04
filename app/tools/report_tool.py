from app.db.vector_db import search_similar
from app.services.rag_service import embed_query
import re


# -------------------------
# CLEAN TEXT
# -------------------------
def clean_text(text: str) -> str:
    text = text.replace("%", "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# -------------------------
# MAIN TOOL
# -------------------------
def analyze_health_report(query: str) -> str:
    print(f"[TOOL EXECUTED] analyze_health_report with query: {query}")

    query_embedding = embed_query(query)
    results = search_similar(query_embedding, top_k=5)

    if not results:
        return "No relevant information found."

    # Return the raw text chunks to the LLM so it can read the report itself!
    # Joining with newlines to separate chunks clearly.
    extracted_text = "\n...\n".join(results)
    
    return extracted_text


# -------------------------
# TOOL SCHEMA (REQUIRED)
# -------------------------
analyze_health_report_schema = {
    "type": "function",
    "function": {
        "name": "analyze_health_report",
        "description": "Analyze medical report and retrieve report text based on the user query.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "User question related to health report"
                }
            },
            "required": ["query"]
        }
    }
}