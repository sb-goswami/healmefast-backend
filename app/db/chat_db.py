import os
from datetime import datetime, timezone
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

def save_chat(session_id: str, title: str, messages: list, user_email: str = None):
    """Inserts or updates a chat session in the DB."""
    if chat_collection is None:
        return
    
    query = {"session_id": session_id}
    if user_email:
        query["user_email"] = user_email

    chat_collection.update_one(
        query,
        {
            "$set": {
                "title": title,
                "messages": messages,
                "updated_at": datetime.now(timezone.utc),
                "user_email": user_email
            },
            "$setOnInsert": {
                "created_at": datetime.now(timezone.utc)
            }
        },
        upsert=True
    )

def get_all_chats(user_email: str = None):
    """Retrieves all chat sessions for a user."""
    if chat_collection is None:
        return []
    
    query = {}
    if user_email:
        query["user_email"] = user_email
        
    chats = chat_collection.find(
        query,
        {"session_id": 1, "title": 1, "updated_at": 1, "_id": 0}
    ).sort("updated_at", DESCENDING)
    
    return list(chats)

def get_chat_by_id(session_id: str, user_email: str = None):
    """Retrieves full chat history for a given session and user."""
    if chat_collection is None:
        return None
    
    query = {"session_id": session_id}
    if user_email:
        query["user_email"] = user_email
        
    return chat_collection.find_one(query, {"_id": 0})

def delete_chat(session_id: str, user_email: str = None):
    """Deletes a chat session by session_id and user."""
    if chat_collection is None:
        return False
    
    query = {"session_id": session_id}
    if user_email:
        query["user_email"] = user_email
        
    result = chat_collection.delete_one(query)
    return result.deleted_count > 0
