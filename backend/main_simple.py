import os
import uvicorn
from dotenv import load_dotenv

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Use synchronous routes to avoid motor issues
from api.routes import router

# Load environment variables
load_dotenv()

app = FastAPI(
    title="SmartRead API (Simple)",
    description="Simple version without async MongoDB",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router)

@app.get("/ping")
async def ping():
    return {"status": "ok", "message": "Simple version running"}

if __name__ == "__main__":
    uvicorn.run(
        "main_simple:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=True,
    )
