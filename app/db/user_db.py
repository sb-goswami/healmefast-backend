import os
from datetime import datetime, timezone
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("DB_NAME", "health_ai_db")
USER_COLLECTION_NAME = "users"

if not MONGODB_URI or "mongodb" not in MONGODB_URI:
    print("[MongoDB WARNING] MONGODB_URI is missing or invalid.")
    client = None
    user_collection = None
else:
    try:
        print(f"[MongoDB User DB] Connecting to {DB_NAME}...")
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        db = client[DB_NAME]
        user_collection = db[USER_COLLECTION_NAME]
        # Create unique index on email
        user_collection.create_index("email", unique=True)
        print("[MongoDB User DB] Connected and index verified.")
    except Exception as e:
        print(f"[MongoDB User DB] Could not connect: {e}")
        user_collection = None

def create_user(user_data: dict):
    if user_collection is None:
        print("[MongoDB User DB] Cannot create user: collection is None")
        return None
    user_data["created_at"] = datetime.now(timezone.utc)
    try:
        print(f"[MongoDB User DB] Inserting user: {user_data.get('email')}")
        result = user_collection.insert_one(user_data)
        print(f"[MongoDB User DB] User inserted with id: {result.inserted_id}")
        return user_data
    except Exception as e:
        print(f"Error creating user in DB: {e}")
        return None

def get_user_by_email(email: str):
    if user_collection is None:
        return None
    return user_collection.find_one({"email": email})

def update_user_password(email: str, new_password_hash: str):
    if user_collection is None:
        return False
    result = user_collection.update_one(
        {"email": email},
        {"$set": {"password": new_password_hash, "updated_at": datetime.now(timezone.utc)}}
    )
    return result.modified_count > 0

def set_reset_token(email: str, token: str, expiry: datetime):
    if user_collection is None:
        return False
    result = user_collection.update_one(
        {"email": email},
        {"$set": {"reset_token": token, "reset_token_expiry": expiry}}
    )
    return result.modified_count > 0

def get_user_by_reset_token(token: str):
    if user_collection is None:
        return None
    return user_collection.find_one({
        "reset_token": token,
        "reset_token_expiry": {"$gt": datetime.now(timezone.utc)}
    })
