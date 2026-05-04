import os
from pymongo import MongoClient
from pymongo.errors import ConfigurationError, ServerSelectionTimeoutError
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("DB_NAME", "health_ai_db")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "medical_docs")

# Use short timeouts so DNS failures don't hang server startup
try:
    client = MongoClient(
        MONGODB_URI,
        serverSelectionTimeoutMS=5000,   # fail fast if can't connect
        connectTimeoutMS=5000,
        socketTimeoutMS=10000,
    )
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    print("[MongoDB] Client created successfully.")
except (ConfigurationError, Exception) as e:
    print(f"[MongoDB WARNING] Could not connect: {e}")
    client = None
    db = None
    collection = None

# Store
def store_embeddings(chunks, embeddings):
    if collection is None:
        print("[MongoDB] Skipping store — no DB connection.")
        return
    docs = []
    for i, chunk in enumerate(chunks):
        docs.append({
            "text": chunk,
            "embedding": embeddings[i].tolist()
        })
    
    if docs:
        collection.insert_many(docs)

# Search
def search_similar(query_embedding, top_k=15):
    if collection is None:
        print("[MongoDB] Skipping search — no DB connection.")
        return []
    pipeline = [
        {
            "$vectorSearch": {
                "index": "vector_index",
                "path": "embedding",
                "queryVector": query_embedding.tolist(),
                "numCandidates": 100,
                "limit": top_k
            }
        },
        {
            "$project": {
                "text": 1,
                "score": {"$meta": "vectorSearchScore"}
            }
        }
    ]
    
    results = list(collection.aggregate(pipeline))
    
    # Fallback: if vector search returns nothing (e.g., index syncing delay or small document),
    # just return the latest chunks directly from the collection.
    if not results:
        results = list(collection.find({}, {"text": 1}).limit(top_k))
        
    return [doc.get("text", "") for doc in results]

def clear_db():
    if collection is None:
        print("[MongoDB] Skipping clear — no DB connection.")
        return
    collection.delete_many({})