from fastapi import APIRouter, UploadFile, File
from app.db.vector_db import store_embeddings, clear_db
import os

from app.services.ocr_service import extract_text
from app.services.rag_service import process_text
from app.db.vector_db import store_embeddings
from app.services.llm_service import generate_initial_analysis

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):

    # 1. Save file
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # 2. OCR extract
    text = extract_text(file_path)

    # 3. RAG processing
    chunks, embeddings = process_text(text)

    clear_db()

    # 4. STORE in vector DB 
    store_embeddings(chunks, embeddings)

    # 4.5 Generate initial analysis
    analysis = generate_initial_analysis(text)

    # 5. Return response
    return {
        "filename": file.filename,
        "total_chunks": len(chunks),
        "sample_chunk": chunks[0] if chunks else "",
        "message": "Stored in vector DB ✅",
        "analysis": analysis
    }