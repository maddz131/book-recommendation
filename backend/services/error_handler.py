"""
Error handling utilities for API errors and exceptions.
"""

import json
import logging
from openai import APIError, APITimeoutError, RateLimitError
from config import OPENAI_MODEL

logger = logging.getLogger(__name__)


class APIErrorHandler:
    """Centralized error handling for OpenAI API errors."""
    
    @staticmethod
    def handle_openai_error(error: Exception) -> str:
        """
        Handle OpenAI API errors and return appropriate error message.
        
        Args:
            error: The exception that was raised
            
        Returns:
            JSON-formatted error message string for SSE streaming
        """
        if isinstance(error, RateLimitError):
            logger.error("OpenAI rate limit exceeded")
            return APIErrorHandler._format_sse_error("API rate limit exceeded. Please try again later.")
        
        elif isinstance(error, APITimeoutError):
            logger.error("OpenAI API timeout")
            return APIErrorHandler._format_sse_error("Request timed out. Please try again.")
        
        elif isinstance(error, APIError):
            logger.error(f"OpenAI API error: {str(error)}")
            return APIErrorHandler._format_sse_error("Error communicating with recommendation service. Please try again later.")
        
        else:
            logger.exception(f"Unexpected OpenAI error: {error}")
            return APIErrorHandler._format_sse_error("An unexpected error occurred. Please try again later.")
    
    @staticmethod
    def handle_stream_error(error: Exception) -> str:
        """
        Handle errors during stream processing.
        
        Args:
            error: The exception that occurred during streaming
            
        Returns:
            JSON-formatted error message string for SSE streaming
        """
        logger.error(f"Error during stream iteration: {str(error)}")
        logger.exception("Stream iteration error details")
        return APIErrorHandler._format_sse_error(f"Error during streaming: {str(error)}")
    
    @staticmethod
    def handle_empty_stream(chunk_count: int) -> str:
        """
        Handle case where stream returns no content.
        
        Args:
            chunk_count: Number of chunks processed
            
        Returns:
            JSON-formatted error message string for SSE streaming
        """
        if chunk_count == 0:
            error_msg = (
                f"No chunks received from API. Model '{OPENAI_MODEL}' may not exist "
                "or may not support streaming. Please check the model name and try again."
            )
            logger.error(error_msg)
            return APIErrorHandler._format_sse_error(error_msg)
        else:
            error_msg = (
                f"Received {chunk_count} chunks but no content. "
                "The model may have returned an empty response."
            )
            logger.error(error_msg)
            return APIErrorHandler._format_sse_error(error_msg)
    
    @staticmethod
    def handle_unexpected_error(error: Exception, context: str = "") -> str:
        """
        Handle unexpected errors with optional context.
        
        Args:
            error: The unexpected exception
            context: Optional context string describing where the error occurred
            
        Returns:
            JSON-formatted error message string for SSE streaming
        """
        log_msg = f"Unexpected error in {context}" if context else "Unexpected error"
        logger.exception(log_msg)
        return APIErrorHandler._format_sse_error("An unexpected error occurred. Please try again later.")
    
    @staticmethod
    def _format_sse_error(message: str) -> str:
        """
        Format error message as SSE data.
        
        Args:
            message: Error message to format
            
        Returns:
            SSE-formatted error string
        """
        error_data = json.dumps({"error": message})
        return f"data: {error_data}\n\n"
    
    @staticmethod
    def handle_openai_error_for_tags(error: Exception) -> tuple[list[str], bool]:
        """
        Handle OpenAI API errors for tags endpoint.
        Returns empty tags list and error flag.
        
        Args:
            error: The exception that was raised
            
        Returns:
            Tuple of (empty tags list, error occurred flag)
        """
        if isinstance(error, RateLimitError):
            logger.error("OpenAI rate limit exceeded while fetching tags")
        elif isinstance(error, APITimeoutError):
            logger.error("OpenAI API timeout while fetching tags")
        elif isinstance(error, APIError):
            logger.error(f"OpenAI API error while fetching tags: {str(error)}")
        else:
            logger.exception("Unexpected error while fetching tags")
        
        return [], True
    
    @staticmethod
    def handle_invalid_response(context: str = "") -> tuple[list[str], bool]:
        """
        Handle invalid response from OpenAI API.
        
        Args:
            context: Optional context describing what was being fetched
            
        Returns:
            Tuple of (empty tags list, error occurred flag)
        """
        log_msg = f"Invalid response from OpenAI API for {context}" if context else "Invalid response from OpenAI API"
        logger.warning(log_msg)
        return [], True
    
    @staticmethod
    def handle_unexpected_error_for_tags(error: Exception, context: str = "") -> tuple[list[str], bool]:
        """
        Handle unexpected errors for tags endpoint.
        Returns empty tags list and error flag.
        
        Args:
            error: The unexpected exception
            context: Optional context string describing where the error occurred
            
        Returns:
            Tuple of (empty tags list, error occurred flag)
        """
        log_msg = f"Unexpected error {context}" if context else "Unexpected error"
        logger.exception(log_msg)
        return [], True
