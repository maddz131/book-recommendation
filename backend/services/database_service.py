"""
Database service for storing recommendations and analytics.
Uses SQLite for simplicity, can be upgraded to PostgreSQL.
"""

import json
import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional

from config import DB_MAX_RECOMMENDATION_LENGTH

logger = logging.getLogger(__name__)

# Database file path
DB_PATH = Path(__file__).resolve().parent.parent / "recommendations.db"


@contextmanager
def get_db_connection():
    """Get a database connection with proper cleanup."""
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_database():
    """Initialize the database with required tables."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Create recommendations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_name TEXT NOT NULL,
                tags TEXT,  -- JSON array of tags
                recommendations_text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                request_count INTEGER DEFAULT 1
            )
        """)
        
        # Create search_history table for analytics
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_name TEXT NOT NULL,
                tags TEXT,  -- JSON array of tags
                searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ip_address TEXT
            )
        """)
        
        # Create indexes for better query performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_book_name ON recommendations(book_name)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_created_at ON recommendations(created_at)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_searched_at ON search_history(searched_at)
        """)
        
        conn.commit()
    logger.info("Database initialized successfully")


def save_recommendations(book_name: str, tags: list[str], recommendations_text: str):
    """
    Save recommendations to the database.
    
    Args:
        book_name: Name of the book
        tags: List of tags
        recommendations_text: Full recommendations text
    """
    try:
        # Truncate recommendations if too long to prevent database bloat
        if len(recommendations_text) > DB_MAX_RECOMMENDATION_LENGTH:
            recommendations_text = recommendations_text[:DB_MAX_RECOMMENDATION_LENGTH]
            logger.warning(f"Truncated recommendations text for {book_name} (exceeded {DB_MAX_RECOMMENDATION_LENGTH} chars)")
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            tags_json = json.dumps(tags) if tags else None
            
            # Check if recommendation already exists
            cursor.execute("""
                SELECT id, request_count FROM recommendations
                WHERE book_name = ? AND tags = ?
            """, (book_name, tags_json))
            
            existing = cursor.fetchone()
            
            if existing:
                # Update existing record
                cursor.execute("""
                    UPDATE recommendations
                    SET recommendations_text = ?, request_count = request_count + 1, created_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (recommendations_text, existing['id']))
            else:
                # Insert new record
                cursor.execute("""
                    INSERT INTO recommendations (book_name, tags, recommendations_text)
                    VALUES (?, ?, ?)
                """, (book_name, tags_json, recommendations_text))
            
            conn.commit()
        logger.debug(f"Saved recommendations for: {book_name}")
    except Exception as e:
        logger.error(f"Error saving recommendations to database: {str(e)}")


def log_search(book_name: str, tags: list[str], ip_address: Optional[str] = None):
    """
    Log a search query for analytics.
    
    Args:
        book_name: Name of the book searched
        tags: List of tags used
        ip_address: Optional IP address of the requester (sanitized)
    """
    try:
        # Sanitize IP address (basic validation)
        if ip_address:
            # Basic IP validation - only store if it looks like a valid IP
            parts = ip_address.split('.')
            if len(parts) != 4 or not all(part.isdigit() and 0 <= int(part) <= 255 for part in parts):
                ip_address = None  # Don't store invalid IPs
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            tags_json = json.dumps(tags) if tags else None
            
            cursor.execute("""
                INSERT INTO search_history (book_name, tags, ip_address)
                VALUES (?, ?, ?)
            """, (book_name, tags_json, ip_address))
            
            conn.commit()
        logger.debug(f"Logged search for: {book_name}")
    except Exception as e:
        logger.error(f"Error logging search to database: {str(e)}")


def get_popular_searches(limit: int = 10) -> list[dict]:
    """
    Get most popular searches.
    
    Args:
        limit: Maximum number of results to return
        
    Returns:
        List of dictionaries with search statistics
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT book_name, COUNT(*) as search_count
            FROM search_history
            GROUP BY book_name
            ORDER BY search_count DESC
            LIMIT ?
        """, (limit,))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    except Exception as e:
        logger.error(f"Error getting popular searches: {str(e)}")
        return []


def get_popular_searches(limit: int = 10) -> list[dict]:
    """
    Get most popular searches.
    
    Args:
        limit: Maximum number of results to return (max 100 for safety)
        
    Returns:
        List of dictionaries with search statistics
    """
    try:
        # Enforce maximum limit for safety
        limit = min(limit, 100)
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT book_name, COUNT(*) as search_count
                FROM search_history
                GROUP BY book_name
                ORDER BY search_count DESC
                LIMIT ?
            """, (limit,))
            
            results = [dict(row) for row in cursor.fetchall()]
        return results
    except Exception as e:
        logger.error(f"Error getting popular searches: {str(e)}")
        return []


def get_recommendation_stats() -> dict:
    """
    Get statistics about stored recommendations.
    
    Returns:
        Dictionary with statistics
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) as total FROM recommendations")
            total_recommendations = cursor.fetchone()['total']
            
            cursor.execute("SELECT SUM(request_count) as total_requests FROM recommendations")
            total_requests = cursor.fetchone()['total_requests'] or 0
            
            cursor.execute("SELECT COUNT(*) as total_searches FROM search_history")
            total_searches = cursor.fetchone()['total_searches']
        
        return {
            "total_recommendations": total_recommendations,
            "total_requests": total_requests,
            "total_searches": total_searches
        }
    except Exception as e:
        logger.error(f"Error getting recommendation stats: {str(e)}")
        return {
            "total_recommendations": 0,
            "total_requests": 0,
            "total_searches": 0
        }


# Initialize database on import
init_database()
