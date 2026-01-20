"""
Book Recommendation API Backend
Uses OpenAI GPT to provide book recommendations based on user input.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from openai import OpenAI, APIError, APITimeoutError, RateLimitError
import os
from dotenv import load_dotenv
from pathlib import Path
import logging

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
OPENAI_MODEL = "gpt-4o-mini"  # Cost-efficient model
OPENAI_TEMPERATURE = 0.7     # Controls randomness (0-1)
OPENAI_MAX_TOKENS = 1200     # Maximum response length
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

# Initialize OpenAI client
# Validate API key before initializing client
api_key = os.getenv("OPENAI_API_KEY")
if not api_key or not api_key.strip():
    raise ValueError(
        "OPENAI_API_KEY not found in environment variables. "
        "Please make sure the .env file exists in the backend directory "
        "and contains: OPENAI_API_KEY=your_key_here"
    )

# Remove any whitespace from API key (common issue)
api_key = api_key.strip()
client = OpenAI(api_key=api_key, timeout=OPENAI_TIMEOUT)
logger.info("OpenAI client initialized successfully")


# Pydantic models for request/response validation
class BookRequest(BaseModel):
    """Request model for book recommendations with input validation."""
    
    book_name: str = Field(
        ...,
        min_length=MIN_BOOK_NAME_LENGTH,
        max_length=MAX_BOOK_NAME_LENGTH,
        description="Name of the book to get recommendations for"
    )
    
    tags: list[str] = Field(
        default=[],
        description="Optional list of tags/genres to filter recommendations by (e.g., romance, sci-fi, mafia)"
    )
    
    @field_validator('book_name')
    @classmethod
    def validate_book_name(cls, v: str) -> str:
        """
        Validate and sanitize book name input.
        
        Args:
            v: The input book name string
            
        Returns:
            Trimmed book name
            
        Raises:
            ValueError: If book name is empty after trimming or contains invalid characters
        """
        # Trim whitespace
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Book name cannot be empty or only whitespace")
        
        # Basic validation: prevent control characters and excessive length
        if len(trimmed) > MAX_BOOK_NAME_LENGTH:
            raise ValueError(f"Book name must be less than {MAX_BOOK_NAME_LENGTH} characters")
        
        # Prevent control characters (except newlines/tabs for book titles with line breaks)
        if any(ord(c) < 32 and c not in '\n\t' for c in trimmed):
            raise ValueError("Book name contains invalid characters")
        
        return trimmed
    
    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v: list[str]) -> list[str]:
        """
        Validate and sanitize tags list.
        
        Args:
            v: List of tag strings
            
        Returns:
            List of trimmed, non-empty, validated tags (max 20 tags, 50 chars each)
            
        Raises:
            ValueError: If tags exceed limits
        """
        if not v:
            return []
        
        # Filter, trim, and normalize tags
        validated_tags = []
        seen = set()
        
        for tag in v:
            if not tag:
                continue
                
            # Trim and normalize
            cleaned = tag.strip().lower()
            
            # Validate tag length (prevent abuse)
            if len(cleaned) > 50:
                continue
            if len(cleaned) < 1:
                continue
            
            # Prevent control characters
            if any(ord(c) < 32 for c in cleaned):
                continue
            
            # Remove duplicates
            if cleaned not in seen:
                seen.add(cleaned)
                validated_tags.append(cleaned)
        
        # Limit total number of tags (prevent abuse)
        if len(validated_tags) > 20:
            validated_tags = validated_tags[:20]
        
        return validated_tags


class BookResponse(BaseModel):
    """Response model for book recommendations."""
    recommendations: str


class TagsRequest(BaseModel):
    """Request model for getting tags for a book/author."""
    
    book_name: str = Field(
        ...,
        min_length=MIN_BOOK_NAME_LENGTH,
        max_length=MAX_BOOK_NAME_LENGTH,
        description="Name of the book or author to get tags for"
    )
    
    @field_validator('book_name')
    @classmethod
    def validate_book_name(cls, v: str) -> str:
        """Validate and sanitize book name input."""
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Book name cannot be empty or only whitespace")
        return trimmed


class TagsResponse(BaseModel):
    """Response model for book tags."""
    tags: list[str]


@app.get("/")
def read_root():
    """Health check endpoint."""
    return {"message": "Book Recommendation API is running"}


@app.post("/api/tags", response_model=TagsResponse)
async def get_tags(request: TagsRequest) -> TagsResponse:
    """
    Get relevant tags/genres for a book or author.
    
    Args:
        request: TagsRequest containing the book/author name
        
    Returns:
        TagsResponse with list of relevant tags (empty list on error)
    """
    try:
        logger.info(f"Fetching tags for: {request.book_name[:50]}...")
        
        # Sanitize input for prompt
        sanitized_book_name = _sanitize_for_prompt(request.book_name)
        
        # Create prompt to extract tags
        prompt = f"""Given the book or author "{sanitized_book_name}", provide a list of 5-10 relevant tags that describe this book/author's genre, themes, or characteristics.

Examples of tags could include:
- Genres: romance, fantasy, sci-fi, mystery, thriller, horror, historical fiction
- Themes: mafia, military, coming-of-age, dystopian, paranormal, contemporary
- Characteristics: dark romance, enemies-to-lovers, found family, heist

Return ONLY a comma-separated list of tags. Do not include any explanation or formatting.
Example format: romance, mafia, dark romance, contemporary, enemies-to-lovers"""
        
        try:
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that identifies book genres, themes, and characteristics."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,  # Lower temperature for more consistent tag extraction
                max_tokens=150
            )
        except (RateLimitError, APITimeoutError, APIError) as e:
            logger.error(f"OpenAI API error while fetching tags: {str(e)}")
            # Return empty tags list on error rather than failing completely
            return TagsResponse(tags=[])
        
        # Extract tags from response
        if not response.choices or not response.choices[0].message.content:
            logger.warning("Invalid response from OpenAI API for tags")
            return TagsResponse(tags=[])
        
        # Parse tags from comma-separated response
        tags_text = response.choices[0].message.content.strip()
        # Split by comma and clean up tags
        tags = [
            tag.strip().lower()
            for tag in tags_text.split(',')
            if tag.strip()
        ]
        
        # Limit to 10 tags maximum
        tags = tags[:10]
        
        logger.info(f"Generated {len(tags)} tags for: {request.book_name}")
        return TagsResponse(tags=tags)
    
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Validation error while fetching tags: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Unexpected error fetching tags")
        # Return empty tags list on unexpected errors
        return TagsResponse(tags=[])


def _sanitize_for_prompt(text: str) -> str:
    """
    Sanitize text for use in OpenAI prompts to prevent injection attacks.
    
    Escapes quotes and removes control characters that could manipulate the prompt.
    
    Args:
        text: Input text to sanitize
        
    Returns:
        Sanitized text safe for use in prompts
    """
    return text.replace('"', '\\"').replace('\n', ' ').replace('\r', '')


def _build_prompt(book_name: str, tags: list[str] = None) -> str:
    """
    Build the OpenAI prompt for book recommendations.
    
    Args:
        book_name: Sanitized book name
        tags: Optional list of tags to filter by
        
    Returns:
        Complete prompt string
    """
    tag_filter_text = ""
    if tags:
        sanitized_tags = [_sanitize_for_prompt(tag) for tag in tags]
        tags_str = ", ".join(sanitized_tags)
        tag_filter_text = f"\n\nIMPORTANT: Only recommend books that match ALL of the following tags/genres: {tags_str}. Filter out any books that don't match these criteria."
    
    return f"""Sorted based on a combination of their Goodreads and Amazon ratings, recommend a list of 5-8 books that someone who likes "{book_name}" would enjoy.{tag_filter_text}

Please consider:
- Similar genre, themes, and writing style
- Books with high ratings (4.0+ stars) on Goodreads and Amazon
- Well-known and well-reviewed books
- Variety in recommendations

For each recommended book, provide:
1. Book title and author
2. Goodreads rating (X.XX/5★) 
3. Amazon rating (X.XX/5★)
4. A brief explanation (1-2 sentences) of why this book is recommended

IMPORTANT FORMATTING RULES:
- Do NOT use asterisks (*), bold markdown (**), or other formatting characters
- Do NOT use quotes around book titles unless the quote is part of the actual title
- Use plain text only - no markdown formatting
- Book titles should be clean and simple: just the title followed by "by Author Name"

Format your response as a numbered list. Example format:
1. Book Title by Author Name
   - Goodreads: X.XX/5★ | Amazon: X.XX/5★
   - Explanation here...

Be concise but informative, and make sure to include actual ratings for each book. Use plain text only - no markdown or special formatting."""


@app.post("/api/recommend", response_model=BookResponse)
async def get_recommendations(request: BookRequest) -> BookResponse:
    """
    Get book recommendations based on a book name and optional tags.
    
    Args:
        request: BookRequest containing the book name and optional tags
        
    Returns:
        BookResponse with recommendations string
        
    Raises:
        HTTPException: If there's an error processing the request
    """
    try:
        # Log request (truncate for privacy)
        log_name = request.book_name[:50] + ('...' if len(request.book_name) > 50 else '')
        logger.info(f"Recommendation request for: {log_name}, tags: {len(request.tags) if request.tags else 0}")
        
        # Sanitize input for prompt injection prevention
        sanitized_book_name = _sanitize_for_prompt(request.book_name)
        
        # Build prompt using helper function
        prompt = _build_prompt(sanitized_book_name, request.tags)

        # Call OpenAI API with error handling for specific error types
        try:
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful book recommendation assistant that provides thoughtful book suggestions based on user preferences."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=OPENAI_TEMPERATURE,
                max_tokens=OPENAI_MAX_TOKENS
            )
        except RateLimitError:
            # Handle rate limiting gracefully
            logger.error("OpenAI rate limit exceeded")
            raise HTTPException(
                status_code=429,
                detail="API rate limit exceeded. Please try again later."
            )
        except APITimeoutError:
            # Handle timeout errors
            logger.error("OpenAI API timeout")
            raise HTTPException(
                status_code=504,
                detail="Request timed out. Please try again."
            )
        except APIError as e:
            # Handle other OpenAI API errors
            logger.error(f"OpenAI API error: {str(e)}")
            raise HTTPException(
                status_code=502,
                detail="Error communicating with recommendation service. Please try again later."
            )
        
        # Extract recommendations from response
        # Check if response is valid before accessing
        if not response.choices or not response.choices[0].message.content:
            logger.error("Invalid response from OpenAI API")
            raise HTTPException(
                status_code=502,
                detail="Invalid response from recommendation service."
            )
        
        recommendations = response.choices[0].message.content
        logger.info(f"Successfully generated recommendations for: {request.book_name}")
        
        return BookResponse(recommendations=recommendations)
    
    except HTTPException:
        # Re-raise HTTP exceptions (already properly formatted)
        raise
    except ValueError as e:
        # Handle validation errors
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Catch-all for unexpected errors
        # Log full error but don't expose internal details to client
        logger.exception("Unexpected error processing recommendation request")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred. Please try again later."
        )


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
