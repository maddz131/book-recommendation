"""
Pydantic models for request/response validation.
"""

from pydantic import BaseModel, Field, field_validator
from config import MAX_BOOK_NAME_LENGTH, MIN_BOOK_NAME_LENGTH


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
