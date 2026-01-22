"""
Prompt building and sanitization utilities.
"""

from config import OPENAI_MODEL


def sanitize_for_prompt(text: str) -> str:
    """
    Sanitize text for use in OpenAI prompts to prevent injection attacks.
    
    Escapes quotes and removes control characters that could manipulate the prompt.
    
    Args:
        text: Input text to sanitize
        
    Returns:
        Sanitized text safe for use in prompts
    """
    return text.replace('"', '\\"').replace('\n', ' ').replace('\r', '')


def build_recommendation_prompt(book_name: str, tags: list[str] = None) -> str:
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
        sanitized_tags = [sanitize_for_prompt(tag) for tag in tags]
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


def build_tags_prompt(book_name: str) -> str:
    """
    Build the OpenAI prompt for extracting tags from a book/author name.
    
    Args:
        book_name: Sanitized book/author name
        
    Returns:
        Complete prompt string for tag extraction
    """
    sanitized_book_name = sanitize_for_prompt(book_name)
    return f"""Given the book or author "{sanitized_book_name}", provide a list of 5-10 relevant tags that describe this book/author's genre, themes, or characteristics.

Examples of tags could include:
- Genres: romance, fantasy, sci-fi, mystery, thriller, horror, historical fiction
- Themes: mafia, military, coming-of-age, dystopian, paranormal, contemporary
- Characteristics: dark romance, enemies-to-lovers, found family, heist

Return ONLY a comma-separated list of tags. Do not include any explanation or formatting.
Example format: romance, mafia, dark romance, contemporary, enemies-to-lovers"""
