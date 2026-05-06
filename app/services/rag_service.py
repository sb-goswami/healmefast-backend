import os
import requests
import numpy as np
from dotenv import load_dotenv, find_dotenv

# Force load the .env file
load_dotenv(find_dotenv(), override=True)

HF_TOKEN = os.getenv("HF_TOKEN")
if not HF_TOKEN:
    print("[WARNING] HF_TOKEN is not set in environment or .env file.")
else:
    print(f"[RAG Service] HF_TOKEN found (Length: {len(HF_TOKEN)})")

from huggingface_hub import InferenceClient

# Using the same model to maintain compatibility with existing vector index
MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"

def get_client():
    # Reload in case it was added after process start
    load_dotenv(find_dotenv(), override=True)
    token = os.getenv("HF_TOKEN")
    if not token:
        print("[HF API WARNING] HF_TOKEN is missing. Requests will likely fail.")
    return InferenceClient(model=MODEL_ID, token=token)

def query_hf_api(payload):
    """Call Hugging Face Inference API using InferenceClient."""
    client = get_client()
    try:
        # feature_extraction expects 'text' or 'inputs'
        inputs = payload.get("inputs", "")
        if isinstance(inputs, list):
            # For lists of strings
            result = client.feature_extraction(inputs)
        else:
            # For a single string
            result = client.feature_extraction(inputs)
        
        # result is usually a list of floats or a list of lists
        return result
    except Exception as e:
        print(f"[HF API Error] {e}")
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