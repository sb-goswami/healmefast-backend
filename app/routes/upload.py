from fastapi import APIRouter, UploadFile, File
from app.db.vector_db import store_embeddings, clear_db
import os
import traceback

from app.services.ocr_service import extract_text
from app.services.rag_service import process_text
from app.services.llm_service import generate_initial_analysis

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    print(f"[Upload] Starting process for: {file.filename}")
    try:
        # 1. Save file
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # 2. OCR extract
        print("[Upload] Running OCR...")
        text = extract_text(file_path)
        if not text or len(text.strip()) < 50:
            print("[Upload WARNING] OCR returned insufficient text.")
            return {
                "filename": file.filename,
                "message": "OCR failed or image quality is too low. Please upload a clearer photo.",
                "analysis": "I couldn't read the report clearly. Please upload a higher-quality photo or PDF so I can provide an accurate analysis."
            }

        # 3. RAG processing
        print(f"[Upload] Processing RAG (Text size: {len(text)})...")
        chunks, embeddings = process_text(text)

        print("[Upload] Cleaning vector DB...")
        clear_db()

        # 4. STORE in vector DB 
        print(f"[Upload] Storing {len(chunks)} chunks...")
        store_embeddings(chunks, embeddings)

        # 4.5 Generate initial analysis
        print("[Upload] Generating LLM analysis...")
        analysis = generate_initial_analysis(text)

        print("[Upload] Finished successfully! ✅")
        # 5. Return response
        return {
            "filename": file.filename,
            "total_chunks": len(chunks),
            "sample_chunk": chunks[0] if chunks else "",
            "message": "Stored in vector DB ✅",
            "analysis": analysis
        }
    except Exception as e:
        print(f"[Upload CRITICAL ERROR] {str(e)}")
        traceback.print_exc()
        return {"error": str(e), "details": "Check server logs for traceback"}, 500