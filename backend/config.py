"""
Configuration constants and environment setup for the Book Recommendation API.
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Configure logging for better debugging and monitoring
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration constants
# These values can be adjusted based on requirements
MAX_BOOK_NAME_LENGTH = 200  # Prevent extremely long inputs
MIN_BOOK_NAME_LENGTH = 1    # Minimum input length
OPENAI_MODEL = "gpt-4o-mini"  # Cost-efficient model (supports gpt-5-nano with higher token limits)
OPENAI_MAX_TOKENS = 2000     # Maximum response length (increase to 8000+ for gpt-5 models that use tokens for reasoning)
OPENAI_TIMEOUT = 30.0       # Timeout in seconds for API calls
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",  # Vite default port
]

# Load environment variables from .env file
# Using resolve() ensures we get the absolute path to the script's directory
script_dir = Path(__file__).resolve().parent
env_path = script_dir / '.env'

# Load environment variables - override=True ensures .env values take precedence
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)
    logger.info(f"Loaded environment variables from {env_path}")
else:
    # Fallback: try loading from current directory
    load_dotenv(override=True)
    logger.warning(".env file not found in backend directory, trying current directory")

# Get OpenAI API key from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY or not OPENAI_API_KEY.strip():
    raise ValueError(
        "OPENAI_API_KEY not found in environment variables. "
        "Please make sure the .env file exists in the backend directory "
        "and contains: OPENAI_API_KEY=your_key_here"
    )

# Redis configuration (optional)
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

# Cache configuration
CACHE_DEFAULT_TTL = int(os.getenv("CACHE_DEFAULT_TTL", "3600"))  # 1 hour default
CACHE_MAX_SIZE = int(os.getenv("CACHE_MAX_SIZE", "1000"))  # Max in-memory cache entries

# Database configuration
DB_MAX_RECOMMENDATION_LENGTH = int(os.getenv("DB_MAX_RECOMMENDATION_LENGTH", "100000"))  # Max chars for recommendations
