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

# Import all route versions
from api.routes import router as original_router
from api.routes_async import router as async_router, limiter as async_limiter
from api.routes_gemini_tavily import router as enhanced_router, limiter as enhanced_limiter
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
    """Enhanced lifespan context manager"""
    # Startup
    logger.info("Starting SmartRead Enhanced API...")
    
    # Initialize connections and check services
    try:
        from utils.db import async_db, redis_client
        
        # Test database connection
        await async_db.command("ping")
        logger.info("✅ Database connection established")
        
        # Test Redis connection
        if redis_client:
            import asyncio
            await asyncio.to_thread(redis_client.ping)
            logger.info("✅ Redis connection established")
        else:
            logger.warning("⚠️  Redis not configured - caching disabled")
        
        # Check Gemini availability
        if os.getenv("GEMINI_API_KEY"):
            logger.info("✅ Gemini API key configured")
        else:
            logger.warning("⚠️  Gemini API key not found")
        
        # Check Tavily availability
        if os.getenv("TAVILY_API_KEY"):
            logger.info("✅ Tavily API key configured")
        else:
            logger.warning("⚠️  Tavily API key not found")
        
        # Check Mistral/Groq availability
        if os.getenv("MISTRAL_API_KEY"):
            logger.info("✅ Mistral API key configured")
        else:
            logger.warning("⚠️  Mistral API key not found")
            
        if os.getenv("GROQ_API_KEY"):
            logger.info("✅ Groq API key configured")
        else:
            logger.warning("⚠️  Groq API key not found")
            
    except Exception as e:
        logger.error(f"❌ Failed to initialize connections: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down SmartRead Enhanced API...")


def determine_router_mode():
    """Determine which router to use based on configuration"""
    mode = os.getenv("PROCESSING_MODE", "auto").lower()
    
    if mode == "enhanced":
        return enhanced_router, enhanced_limiter, "Enhanced (Gemini + Tavily)"
    elif mode == "async":
        return async_router, async_limiter, "Async (Mistral + Groq + Redis)"
    elif mode == "original":
        return original_router, None, "Original (Mistral + Groq)"
    else:  # auto mode
        # Auto-select based on available API keys
        has_gemini = bool(os.getenv("GEMINI_API_KEY"))
        has_tavily = bool(os.getenv("TAVILY_API_KEY"))
        has_mistral = bool(os.getenv("MISTRAL_API_KEY"))
        has_groq = bool(os.getenv("GROQ_API_KEY"))
        
        if has_gemini and has_tavily:
            return enhanced_router, enhanced_limiter, "Enhanced (Auto-selected)"
        elif has_mistral and has_groq:
            return async_router, async_limiter, "Async (Auto-selected)"
        else:
            return original_router, None, "Original (Auto-selected)"


def create_application() -> FastAPI:
    """Create and configure the enhanced FastAPI application"""
    
    # Determine router and mode
    router, limiter, mode_description = determine_router_mode()
    
    app = FastAPI(
        title="SmartRead Enhanced API",
        description=f"AI-powered document processing with multiple backends - {mode_description}",
        version="3.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Add middleware
    setup_middleware(app)
    
    # Include routes
    app.include_router(router)
    
    # Add rate limiting if available
    if limiter:
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
    
    # Add startup info endpoint
    @app.get("/info")
    async def app_info():
        """Get application information"""
        return {
            "name": "SmartRead Enhanced API",
            "version": "3.0.0",
            "mode": mode_description,
            "features": {
                "gemini_processing": bool(os.getenv("GEMINI_API_KEY")),
                "tavily_search": bool(os.getenv("TAVILY_API_KEY")),
                "mistral_ocr": bool(os.getenv("MISTRAL_API_KEY")),
                "groq_processing": bool(os.getenv("GROQ_API_KEY")),
                "redis_caching": bool(os.getenv("REDIS_URL")),
                "rate_limiting": limiter is not None
            },
            "endpoints": {
                "health": "/health",
                "enhanced_health": "/health/enhanced",
                "extract": "/api/extract",
                "download": "/pdf/download",
                "search": "/api/search",
                "docs": "/docs"
            }
        }
    
    return app


def setup_middleware(app: FastAPI):
    """Setup enhanced middleware"""
    
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
    
    # Enhanced request logging middleware
    @app.middleware("http")
    async def enhanced_log_requests(request: Request, call_next):
        start_time = time.time()
        
        # Log request
        logger.info(f"📥 {request.method} {request.url.path} - Client: {request.client.host}")
        
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Log response with performance metrics
        status_emoji = "✅" if response.status_code < 400 else "❌"
        logger.info(
            f"📤 {status_emoji} {request.method} {request.url.path} - "
            f"Status: {response.status_code} - "
            f"Time: {process_time:.3f}s"
        )
        
        # Add performance headers
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-SmartRead-Version"] = "3.0.0"
        
        return response


# Create the application instance
app = create_application()


# Enhanced health check endpoint
@app.get("/ping")
async def ping():
    """Simple ping endpoint for load balancers"""
    return {
        "status": "ok", 
        "message": "pong",
        "version": "3.0.0",
        "timestamp": time.time()
    }


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


# Configuration endpoint
@app.get("/config")
async def get_config():
    """Get current configuration (non-sensitive)"""
    return {
        "processing_mode": os.getenv("PROCESSING_MODE", "auto"),
        "environment": os.getenv("ENVIRONMENT", "development"),
        "features_enabled": {
            "gemini": bool(os.getenv("GEMINI_API_KEY")),
            "tavily": bool(os.getenv("TAVILY_API_KEY")),
            "mistral": bool(os.getenv("MISTRAL_API_KEY")),
            "groq": bool(os.getenv("GROQ_API_KEY")),
            "redis": bool(os.getenv("REDIS_URL")),
            "cloudinary": bool(os.getenv("CLOUDINARY_API_KEY"))
        },
        "rate_limiting": {
            "enabled": bool(os.getenv("ENABLE_RATE_LIMITING", "true").lower() == "true"),
            "requests_per_minute": int(os.getenv("RATE_LIMIT_REQUESTS", "10"))
        }
    }


if __name__ == "__main__":
    # Enhanced configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    reload = os.getenv("ENVIRONMENT", "development") == "development"
    workers = int(os.getenv("WORKERS", 1))
    log_level = os.getenv("LOG_LEVEL", "info").lower()
    
    # Display startup information
    print("\n" + "="*60)
    print("🚀 SmartRead Enhanced API Starting...")
    print("="*60)
    print(f"📍 Host: {host}:{port}")
    print(f"🔧 Mode: {os.getenv('PROCESSING_MODE', 'auto')}")
    print(f"🌍 Environment: {os.getenv('ENVIRONMENT', 'development')}")
    print(f"👥 Workers: {workers}")
    print(f"📝 Log Level: {log_level}")
    print("="*60)
    
    # Run the application
    uvicorn.run(
        "main_enhanced:app",
        host=host,
        port=port,
        reload=reload,
        workers=workers if not reload else 1,
        log_level=log_level,
        access_log=True,
    )
