"""
Book Recommendation API Backend
Uses OpenAI GPT to provide book recommendations based on user input.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
import json
import asyncio
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
                # Note: gpt-5 models only support temperature=1 (default), so we don't set it
                max_completion_tokens=150
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
5. The EXACT official book blurb/synopsis from Goodreads.com (you MUST copy the real blurb from Goodreads.com from your training data, do NOT create or summarize)

IMPORTANT FORMATTING RULES:
- Do NOT use asterisks (*), bold markdown (**), or other formatting characters
- Do NOT use quotes around book titles unless the quote is part of the actual title
- Use plain text only - no markdown formatting
- Book titles should be clean and simple: just the title followed by "by Author Name"

Format your response as a numbered list. Example format:
1. Book Title by Author Name
   - Goodreads: X.XX/5★ | Amazon: X.XX/5★
   - Explanation here...
   Blurb: [PASTE THE EXACT OFFICIAL BLURB FROM GOODREADS.COM HERE - DO NOT CREATE YOUR OWN]

CRITICAL BLURB REQUIREMENTS (VIOLATION WILL RESULT IN INCORRECT RESPONSE):
- You MUST copy the EXACT official book blurb/synopsis from Goodreads.com from your training data
- PRIMARY SOURCE: Use Goodreads.com blurbs ONLY - they are the authoritative source for this task
- DO NOT use Amazon.com blurbs - use Goodreads.com blurbs only
- DO NOT write, create, generate, compose, summarize, describe, explain, or invent a blurb
- DO NOT paraphrase, reword, rewrite, or restate the blurb
- DO NOT create content based on your knowledge, memory, or understanding of the book
- DO NOT write your own description or summary from memory
- You MUST use the literal, exact text from Goodreads.com book pages as it appears in your training data
- If the exact official Goodreads.com blurb is not available in your training data, you MUST write "Blurb not available" - DO NOT create, write, or generate anything else
- The blurb text should start with "Blurb: " (NO dash or bullet) followed by the exact text on separate lines
- Copy the blurb word-for-word, preserving all original formatting, punctuation, and paragraph breaks
- DO NOT add dashes, bullets, or quotes around the blurb text - just paste it as plain text
- This is NOT a writing exercise - you are ONLY a copy function, paste the existing Goodreads.com blurb ONLY
- If you cannot find the exact official blurb from Goodreads.com in your training data, write "Blurb not available" - DO NOT write anything else

Be concise but informative, and make sure to include actual ratings and real blurbs for each book. Use plain text only - no markdown or special formatting."""


async def _stream_recommendations(book_name: str, tags: list[str]):
    """
    Stream recommendations from OpenAI API.
    
    First fetches and sends tags, then streams book recommendations.
    Generator function that yields chunks as they arrive.
    """
    try:
        # Sanitize input for prompt injection prevention
        sanitized_book_name = _sanitize_for_prompt(book_name)
        
        # Fetch tags first (only if not provided in request)
        if not tags:
            try:
                tags_prompt = f"""Given the book or author "{sanitized_book_name}", provide a list of 5-10 relevant tags that describe this book/author's genre, themes, or characteristics.

Examples of tags could include:
- Genres: romance, fantasy, sci-fi, mystery, thriller, horror, historical fiction
- Themes: mafia, military, coming-of-age, dystopian, paranormal, contemporary
- Characteristics: dark romance, enemies-to-lovers, found family, heist

Return ONLY a comma-separated list of tags. Do not include any explanation or formatting.
Example format: romance, mafia, dark romance, contemporary, enemies-to-lovers"""
                
                tags_response = client.chat.completions.create(
                    model=OPENAI_MODEL,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a helpful assistant that identifies book genres, themes, and characteristics."
                        },
                        {"role": "user", "content": tags_prompt}
                    ],
                    # Note: gpt-5 models only support temperature=1 (default), so we don't set it
                    max_completion_tokens=150
                )
                
                if tags_response.choices and tags_response.choices[0].message.content:
                    tags_text = tags_response.choices[0].message.content.strip()
                    # Parse tags from comma-separated response
                    tags = [
                        tag.strip().lower()
                        for tag in tags_text.split(',')
                        if tag.strip()
                    ]
                    # Limit to 10 tags maximum
                    tags = tags[:10]
                    
                    # Send tags as first data in stream
                    tags_data = json.dumps({"tags": tags})
                    yield f"data: {tags_data}\n\n"
                    
                    logger.info(f"Generated {len(tags)} tags for: {book_name}")
            except Exception as e:
                # If tag fetching fails, continue without tags
                logger.warning(f"Failed to fetch tags: {str(e)}")
                tags = []
        
        # Build prompt using helper function
        prompt = _build_prompt(sanitized_book_name, tags)
        
        # Call OpenAI API with streaming enabled for recommendations
        try:
            # Build API parameters based on model type
            api_params = {
                "model": OPENAI_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a book recommendation assistant. Each request is completely independent - you have no memory of previous requests or conversations. Treat each new search as brand new with no context from previous searches. CRITICAL RULE FOR BLURBS: You MUST copy the EXACT official book blurb/synopsis from Goodreads.com from your training data. Use Goodreads.com blurbs ONLY - they are the authoritative source. DO NOT use Amazon.com blurbs. DO NOT create, write, generate, summarize, paraphrase, or write blurbs from memory. You are ONLY a copy function - paste the exact existing blurb text word-for-word exactly as it appears on Goodreads.com. If the exact official Goodreads.com blurb is not in your training data, write 'Blurb not available' instead of creating one. DO NOT write your own description or summary - ONLY copy the official Goodreads.com blurb."
                    },
                    {"role": "user", "content": prompt}
                ],
                "stream": True  # Enable streaming
            }
            
            # Use max_tokens for gpt-4/gpt-3.5 models, max_completion_tokens for gpt-5 models
            if "gpt-5" in OPENAI_MODEL:
                api_params["max_completion_tokens"] = OPENAI_MAX_TOKENS
            else:
                api_params["max_tokens"] = OPENAI_MAX_TOKENS
            
            stream = client.chat.completions.create(**api_params)
        except RateLimitError:
            # Handle rate limiting gracefully
            logger.error("OpenAI rate limit exceeded")
            error_data = json.dumps({"error": "API rate limit exceeded. Please try again later."})
            yield f"data: {error_data}\n\n"
            return
        except APITimeoutError:
            # Handle timeout errors
            logger.error("OpenAI API timeout")
            error_data = json.dumps({"error": "Request timed out. Please try again."})
            yield f"data: {error_data}\n\n"
            return
        except APIError as e:
            # Handle other OpenAI API errors
            logger.error(f"OpenAI API error: {str(e)}")
            error_data = json.dumps({"error": "Error communicating with recommendation service. Please try again later."})
            yield f"data: {error_data}\n\n"
            return
        
        # Stream chunks from OpenAI
        accumulated_text = ""
        chunk_count = 0
        
        try:
            for chunk in stream:
                chunk_count += 1
                
                # Check if chunk has choices
                if not chunk.choices or len(chunk.choices) == 0:
                    logger.debug(f"Chunk {chunk_count} has no choices")
                    continue
                
                choice = chunk.choices[0]
                delta = choice.delta
                if not delta:
                    logger.debug(f"Chunk {chunk_count} has no delta")
                    continue
                
                # Check for content in delta - try multiple ways to access it
                content = None
                if hasattr(delta, 'content'):
                    content = delta.content
                elif hasattr(delta, 'text'):
                    content = delta.text
                
                if content:
                    accumulated_text += content
                    # Send chunk as JSON via SSE
                    chunk_data = json.dumps({"chunk": content, "text": accumulated_text})
                    yield f"data: {chunk_data}\n\n"
                else:
                    logger.debug(f"Chunk {chunk_count} delta has no content")
                
                # Small delay to prevent overwhelming the client
                await asyncio.sleep(0.01)
        except Exception as stream_error:
            logger.error(f"Error during stream iteration: {str(stream_error)}")
            logger.exception("Stream iteration error details")
            error_data = json.dumps({"error": f"Error during streaming: {str(stream_error)}"})
            yield f"data: {error_data}\n\n"
            return
        
        # Log stream statistics
        logger.info(f"Stream completed: {chunk_count} chunks processed, {len(accumulated_text)} characters accumulated for: {book_name}")
        
        if not accumulated_text:
            logger.warning(f"No content accumulated from stream for: {book_name}. Chunks processed: {chunk_count}")
            if chunk_count == 0:
                error_msg = f"No chunks received from API. Model '{OPENAI_MODEL}' may not exist or may not support streaming. Please check the model name and try again."
                logger.error(error_msg)
                error_data = json.dumps({"error": error_msg})
                yield f"data: {error_data}\n\n"
                return
            else:
                error_msg = f"Received {chunk_count} chunks but no content. The model may have returned an empty response."
                logger.error(error_msg)
                error_data = json.dumps({"error": error_msg})
                yield f"data: {error_data}\n\n"
                return
        
        # Send final completion signal
        completion_data = json.dumps({"done": True, "text": accumulated_text})
        yield f"data: {completion_data}\n\n"
        
        logger.info(f"Successfully streamed recommendations for: {book_name}")
    
    except Exception as e:
        # Catch-all for unexpected errors
        logger.exception("Unexpected error in streaming recommendations")
        error_data = json.dumps({"error": "An unexpected error occurred. Please try again later."})
        yield f"data: {error_data}\n\n"


@app.post("/api/recommend")
async def get_recommendations(request: BookRequest):
    """
    Get book recommendations based on a book name and optional tags.
    Returns a streaming response with recommendations as they are generated.
    
    Args:
        request: BookRequest containing the book name and optional tags
    
    Returns:
        StreamingResponse with Server-Sent Events (SSE) containing recommendation chunks
        
    Raises:
        HTTPException: If there's a validation error
    """
    try:
        # Log request (truncate for privacy)
        log_name = request.book_name[:50] + ('...' if len(request.book_name) > 50 else '')
        logger.info(f"Recommendation request for: {log_name}, tags: {len(request.tags) if request.tags else 0}")
        
        # Return streaming response
        return StreamingResponse(
            _stream_recommendations(request.book_name, request.tags),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # Disable nginx buffering
            }
        )
    
    except ValueError as e:
        # Handle validation errors
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Catch-all for unexpected errors
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
