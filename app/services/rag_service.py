import os
import requests
import numpy as np
from dotenv import load_dotenv
import time

load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")
# Using the same model to maintain compatibility with existing vector index
MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
API_URL = f"https://api-inference.huggingface.co/models/{MODEL_ID}"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

def query_hf_api(payload):
    """Call Hugging Face Inference API with retries for cold starts."""
    for attempt in range(3):
        response = requests.post(API_URL, headers=headers, json=payload)
        result = response.json()
        
        # Handle model loading (cold start)
        if isinstance(result, dict) and "estimated_time" in result:
            wait_time = result.get("estimated_time", 5)
            print(f"[HF API] Model is loading... waiting {wait_time}s (Attempt {attempt+1}/3)")
            time.sleep(wait_time)
            continue
            
        if response.status_code != 200:
            print(f"[HF API Error] {result}")
            return None
            
        return result
    return None

# 🔹 Chunking
def chunk_text(text, chunk_size=500, overlap=100):
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap

    return chunks


# 🔹 Embeddings for chunks
def generate_embeddings(chunks):
    """Generate embeddings for a list of text chunks."""
    if not chunks:
        return np.array([])
        
    result = query_hf_api({"inputs": chunks, "options": {"wait_for_model": True}})
    if result is None:
        raise Exception("Failed to generate embeddings via Hugging Face API")
        
    return np.array(result)


# 🔹 Embedding for query
def embed_query(query):
    """Generate embedding for a single query."""
    result = query_hf_api({"inputs": [query], "options": {"wait_for_model": True}})
    if result is None:
        raise Exception("Failed to generate query embedding via Hugging Face API")
        
    return np.array(result[0])


# 🔹 Full process
def process_text(text):
    chunks = chunk_text(text)
    embeddings = generate_embeddings(chunks)
    return chunks, embeddings