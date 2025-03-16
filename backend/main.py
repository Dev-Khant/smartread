import os
import uvicorn
from dotenv import load_dotenv

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routes import router
from api.swagger import custom_openapi

# Load environment variables
load_dotenv()


def get_application() -> FastAPI:
    app = FastAPI(
        title="SmartRead API",
        description="API for extracting and processing text from images using Mistral OCR",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Configure CORS with more permissive settings for development
    origins = [
        "http://localhost:3000",  # React default port
        "http://127.0.0.1:3000",
        "http://localhost:5173",  # Vite default port
        "http://127.0.0.1:5173",
        "https://smartread-beta.vercel.app",
    ]

    if os.getenv("ENVIRONMENT") == "development":
        # In development, you might want to allow all origins
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
            expose_headers=["*"],
            max_age=3600,
        )
    else:
        # In production, be more restrictive
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            allow_headers=["Authorization", "Content-Type"],
            expose_headers=["*"],
            max_age=3600,
        )

    # Include routes
    app.include_router(router)

    # Configure custom OpenAPI
    app.openapi = lambda: custom_openapi(app)

    return app


app = get_application()


@app.options("/{path:path}")
async def options_handler(path: str):
    return JSONResponse(
        status_code=200,
        content={"message": "OK"},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Authorization, Content-Type",
        },
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=str(os.getenv("HOST")),
        port=int(os.getenv("PORT")),
        reload=True,  # Enable auto-reload
        reload_dirs=["api"],  # Watch the api directory for changes
        workers=1,  # Use single worker for development
        log_level="debug",  # More detailed logging
    )
