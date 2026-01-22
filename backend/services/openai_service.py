"""
OpenAI service for handling API interactions with connection pooling.
"""

import logging
from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_TIMEOUT

logger = logging.getLogger(__name__)

# Try to use httpx for connection pooling if available
try:
    import httpx
    
    # Create httpx client with connection pooling for better performance
    http_client = httpx.Client(
        limits=httpx.Limits(
            max_keepalive_connections=20,
            max_connections=100,
            keepalive_expiry=30.0
        ),
        timeout=httpx.Timeout(OPENAI_TIMEOUT, connect=10.0)
    )
    
    # Initialize OpenAI client with connection pooling
    client = OpenAI(
        api_key=OPENAI_API_KEY,
        timeout=OPENAI_TIMEOUT,
        http_client=http_client
    )
    logger.info("OpenAI client initialized with connection pooling")
except ImportError:
    # Fallback to default client if httpx is not available
    client = OpenAI(api_key=OPENAI_API_KEY, timeout=OPENAI_TIMEOUT)
    logger.info("OpenAI client initialized (httpx not available, using default client)")
