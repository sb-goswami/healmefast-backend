from sentence_transformers import SentenceTransformer
import numpy as np

# Load model
model = SentenceTransformer("all-MiniLM-L6-v2")


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
    return model.encode(chunks)


# 🔹 Embedding for query
def embed_query(query):
    return model.encode(query)


# 🔹 Full process
def process_text(text):
    chunks = chunk_text(text)
    embeddings = generate_embeddings(chunks)
    return chunks, embeddings