"""
Recommendations endpoint router.
"""

import json
import asyncio
import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from models import BookRequest
from services.openai_service import client
from services.prompt_service import build_recommendation_prompt, sanitize_for_prompt, build_tags_prompt
from config import OPENAI_MODEL, OPENAI_MAX_TOKENS
from openai import APIError, APITimeoutError, RateLimitError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["recommendations"])


async def _stream_recommendations(book_name: str, tags: list[str]):
    """
    Stream recommendations from OpenAI API.
    
    First fetches and sends tags, then streams book recommendations.
    Generator function that yields chunks as they arrive.
    """
    try:
        # Sanitize input for prompt injection prevention
        sanitized_book_name = sanitize_for_prompt(book_name)
        
        # Fetch tags first (only if not provided in request)
        if not tags:
            try:
                tags_prompt = build_tags_prompt(sanitized_book_name)
                
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
        prompt = build_recommendation_prompt(sanitized_book_name, tags)
        
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


@router.post("/recommend")
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
