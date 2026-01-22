"""
Book Recommendation API Backend
Uses OpenAI GPT to provide book recommendations based on user input.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import logging
from config import ALLOWED_ORIGINS
from routers import tags, recommendations

# Configure logging for better debugging and monitoring
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Try to import rate limiting, fallback if not available
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    
    limiter = Limiter(key_func=get_remote_address)
    RATE_LIMITING_AVAILABLE = True
except ImportError:
    limiter = None
    RATE_LIMITING_AVAILABLE = False
    logger.warning("slowapi not installed, rate limiting disabled")

# Initialize FastAPI application
app = FastAPI(
    title="Book Recommendation API",
    description="API for getting book recommendations using OpenAI",
    version="1.0.0"
)

# Configure CORS (Cross-Origin Resource Sharing)
# In production, replace ALLOWED_ORIGINS with specific frontend URLs
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # Only allow necessary methods
    allow_headers=["Content-Type", "Authorization"],  # Restrict headers
)

# Add compression middleware for better performance
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Configure rate limiting if available
if RATE_LIMITING_AVAILABLE:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Include routers
app.include_router(tags.router)
app.include_router(recommendations.router)


@app.get("/")
def read_root():
    """Health check endpoint."""
    return {"message": "Book Recommendation API is running"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler to catch any unhandled exceptions.
    
    This prevents internal error details from being exposed to clients.
    """
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please try again later."}
    )


if __name__ == "__main__":
    import uvicorn
    # Run the server
    # In production, use a production ASGI server like gunicorn with uvicorn workers
    uvicorn.run(
        app,
        host="0.0.0.0",  # Listen on all interfaces
        port=8000,
        log_level="info"
    )
