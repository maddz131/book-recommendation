"""
Tags endpoint router.
"""

import logging
from fastapi import APIRouter, HTTPException
from models import TagsRequest, TagsResponse
from services.openai_service import client
from services.prompt_service import build_tags_prompt, sanitize_for_prompt
from config import OPENAI_MODEL
from openai import APIError, APITimeoutError, RateLimitError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["tags"])


@router.post("/tags", response_model=TagsResponse)
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
        sanitized_book_name = sanitize_for_prompt(request.book_name)
        
        # Create prompt to extract tags
        prompt = build_tags_prompt(sanitized_book_name)
        
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
