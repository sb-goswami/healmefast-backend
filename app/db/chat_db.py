import os
from datetime import datetime
from pymongo import MongoClient, DESCENDING

from dotenv import load_dotenv

load_dotenv()

# Assuming MONGODB_URI and DB_NAME are already loaded via vector_db or main
MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("DB_NAME", "health_ai_db")
CHAT_COLLECTION_NAME = "chat_history"

# Validation: Default to None if empty to avoid localhost fallback
if not MONGODB_URI or "mongodb" not in MONGODB_URI:
    print("[MongoDB WARNING] MONGODB_URI is missing or invalid. Chat history will not be saved.")
    client = None
    chat_collection = None
else:
    try:
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        db = client[DB_NAME]
        chat_collection = db[CHAT_COLLECTION_NAME]
    except Exception as e:
        print(f"[MongoDB Chat DB] Could not connect: {e}")
        chat_collection = None

def save_chat(session_id: str, title: str, messages: list):
    """Inserts or updates a chat session in the DB."""
    if chat_collection is None:
        return
    
    chat_collection.update_one(
        {"session_id": session_id},
        {
            "$set": {
                "title": title,
                "messages": messages,
                "updated_at": datetime.utcnow()
            },
            "$setOnInsert": {
                "created_at": datetime.utcnow()
            }
        },
        upsert=True
    )

def get_all_chats():
    """Retrieves all chat sessions (only session_id, title, updated_at)."""
    if chat_collection is None:
        return []
    
    chats = chat_collection.find(
        {},
        {"session_id": 1, "title": 1, "updated_at": 1, "_id": 0}
    ).sort("updated_at", DESCENDING)
    
    return list(chats)

def get_chat_by_id(session_id: str):
    """Retrieves full chat history for a given session."""
    if chat_collection is None:
        return None
    
    return chat_collection.find_one({"session_id": session_id}, {"_id": 0})
