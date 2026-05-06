from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import upload, chat
import os
import uvicorn

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router)
app.include_router(chat.router)

@app.get("/")
def read_root():
    return {"status": "online", "message": "Health AI Backend is running"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)