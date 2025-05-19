import os
import time
import logging
import uvicorn
from contextlib import asynccontextmanager
from dotenv import load_dotenv

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Import both route versions
from api.routes import router as sync_router
from api.routes_async import router as async_router, limiter
from api.swagger import custom_openapi

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    logger.info("Starting SmartRead API...")

    # Initialize connections
    try:
        from utils.db import async_db, redis_client

        # Test database connection
        await async_db.command("ping")
        logger.info("Database connection established")

        # Test Redis connection
        if redis_client:
            import asyncio
            await asyncio.to_thread(redis_client.ping)
            logger.info("Redis connection established")
        else:
            logger.warning("Redis not configured - caching disabled")

    except Exception as e:
        logger.error(f"Failed to initialize connections: {e}")

    yield

    # Shutdown
    logger.info("Shutting down SmartRead API...")


def create_application() -> FastAPI:
    """Create and configure the FastAPI application"""

    # Determine which router to use based on environment
    use_async = os.getenv("USE_ASYNC_ROUTES", "true").lower() == "true"
    router = async_router if use_async else sync_router

    app = FastAPI(
        title="SmartRead API",
        description="AI-powered tool for annotating technical PDFs with related resources",
        version="2.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Add middleware
    setup_middleware(app)

    # Include routes
    app.include_router(router)

    # Add rate limiting
    if use_async:
        app.state.limiter = limiter
        app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Configure custom OpenAPI
    app.openapi = lambda: custom_openapi(app)

    # Add global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Global exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )

    return app


def setup_middleware(app: FastAPI):
    """Setup middleware for the application"""

    # CORS middleware
    origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://smartread-beta.vercel.app",
    ]

    # Add environment-specific origins
    if custom_origins := os.getenv("ALLOWED_ORIGINS"):
        origins.extend(custom_origins.split(","))

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
        expose_headers=["*"],
        max_age=3600,
    )

    # Compression middleware
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # Request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time

        logger.info(
            f"{request.method} {request.url.path} - "
            f"Status: {response.status_code} - "
            f"Time: {process_time:.3f}s"
        )
        return response


# Create the application instance
app = create_application()


# Health check endpoint
@app.get("/ping")
async def ping():
    """Simple ping endpoint for load balancers"""
    return {"status": "ok", "message": "pong"}


# Options handler for CORS preflight
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
    # Configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    reload = os.getenv("ENVIRONMENT", "development") == "development"
    workers = int(os.getenv("WORKERS", 1))

    # Run the application
    uvicorn.run(
        "main_improved:app",
        host=host,
        port=port,
        reload=reload,
        workers=workers if not reload else 1,  # Single worker for development
        log_level="info",
        access_log=True,
    )
