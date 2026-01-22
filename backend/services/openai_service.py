"""
OpenAI service for handling API interactions.
"""

import logging
from openai import OpenAI, APIError, APITimeoutError, RateLimitError
from config import OPENAI_API_KEY, OPENAI_TIMEOUT

logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY, timeout=OPENAI_TIMEOUT)
logger.info("OpenAI client initialized successfully")
