from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import upload, chat, auth
import os
import uvicorn

app = FastAPI()

# CORS
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://healmefast-frontend.vercel.app",
]
frontend_url = os.getenv("FRONTEND_URL")
if frontend_url:
    # Clean up the URL: remove quotes, whitespace, and trailing slashes
    clean_url = frontend_url.strip().replace('"', '').replace("'", "").rstrip("/")
    if clean_url:
        origins.append(clean_url)
        print(f"[CORS] Allowed Origin added: {clean_url}")

# If we are in production but FRONTEND_URL is missing, warn but allow local for safety
print(f"[CORS] Final allowed origins: {origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router)
app.include_router(chat.router)
app.include_router(auth.router)

@app.get("/")
def read_root():
    return {"status": "online", "message": "Health AI Backend is running"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)