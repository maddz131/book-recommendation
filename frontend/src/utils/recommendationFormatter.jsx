/**
 * Recommendation Formatter Utility
 * 
 * Formats recommendations text into structured data with clickable rating links.
 */

import React from 'react'

/**
 * Cleans markdown and formatting from text
 */
function cleanMarkdown(text) {
  let cleaned = text.replace(/\*+/g, '')
  cleaned = cleaned.replace(/^["'](.+)["']$/g, '$1')
  cleaned = cleaned.replace(/[_~`]/g, '')
  return cleaned.trim()
}

/**
 * Extracts book title and author from a numbered list item line
 */
function extractBookInfo(line) {
  const cleanedLine = cleanMarkdown(line)
  
  // Match pattern like: 1. Book Title by Author Name
  const match = cleanedLine.match(/^\d+\.\s*(.+?)\s+by\s+(.+)$/i)
  if (match) {
    return {
      title: cleanMarkdown(match[1]),
      author: cleanMarkdown(match[2])
    }
  }
  
  // Fallback: extract text after number and period
  const fallbackMatch = cleanedLine.match(/^\d+\.\s*(.+)/)
  if (fallbackMatch) {
    const fullText = fallbackMatch[1]
    const byMatch = fullText.match(/(.+?)\s+by\s+(.+)/i)
    if (byMatch) {
      return {
        title: cleanMarkdown(byMatch[1]),
        author: cleanMarkdown(byMatch[2])
      }
    }
    return {
      title: cleanMarkdown(fullText),
      author: ''
    }
  }
  return { title: '', author: '' }
}

/**
 * Creates search URLs for Goodreads or Amazon
 */
function createSearchUrl(domain, bookTitle, bookAuthor) {
  // Goodreads: use only book title (no author)
  // Amazon: use book title and author
  const searchQuery = domain === 'goodreads' 
    ? bookTitle 
    : (bookAuthor ? `${bookTitle} ${bookAuthor}` : bookTitle)
  const encodedQuery = encodeURIComponent(searchQuery)
  
  if (domain === 'goodreads') {
    return `https://www.goodreads.com/search?q=${encodedQuery}`
  }
  return `https://www.amazon.com/s?k=${encodedQuery}&i=stripbooks`
}

/**
 * Extracts and formats ratings with clickable links
 */
export function extractRatings(details, bookTitle, bookAuthor) {
  const ratings = {
    goodreads: null,
    amazon: null
  }
  
  // Look for rating lines in details
  for (const detail of details) {
    // Match Goodreads rating (with or without stars symbol)
    const goodreadsMatch = detail.match(/Goodreads:\s*([\d.]+)\/5\s*(?:★|star|stars)?/i)
    if (goodreadsMatch && !ratings.goodreads) {
      const rawValue = parseFloat(goodreadsMatch[1])
      const ratingValue = isNaN(rawValue) ? goodreadsMatch[1] : rawValue.toFixed(1)
      ratings.goodreads = {
        value: ratingValue,
        display: `Goodreads: ${ratingValue}/5★`,
        url: createSearchUrl('goodreads', bookTitle, bookAuthor)
      }
    }
    
    // Match Amazon rating (with or without stars symbol)
    const amazonMatch = detail.match(/Amazon:\s*([\d.]+)\/5\s*(?:★|star|stars)?/i)
    if (amazonMatch && !ratings.amazon) {
      const rawValue = parseFloat(amazonMatch[1])
      const ratingValue = isNaN(rawValue) ? amazonMatch[1] : rawValue.toFixed(1)
      ratings.amazon = {
        value: ratingValue,
        display: `Amazon: ${ratingValue}/5★`,
        url: createSearchUrl('amazon', bookTitle, bookAuthor)
      }
    }
  }
  
  return ratings
}

/**
 * Formats a rating line with clickable links
 */
function formatRatingLine(line, bookTitle, bookAuthor) {
  // Only replace "stars" with star symbol in rating patterns
  let formattedLine = line
  
  // Replace stars only in rating context (e.g., "4.5/5 stars" or "Goodreads: 4.5/5 star")
  formattedLine = formattedLine.replace(/(Goodreads|Amazon):\s*([\d.]+\/5)\s*(?:stars?|★)/gi, (match, platform, rating) => {
    return `${platform}: ${rating}★`
  })
  
  // Also handle standalone rating patterns
  formattedLine = formattedLine.replace(/([\d.]+\/5)\s*(?:stars?)\b/gi, '$1★')
  
  // Check if this line contains ratings
  const goodreadsMatch = formattedLine.match(/(Goodreads:\s*[\d.]+\/5★?)/i)
  const amazonMatch = formattedLine.match(/(Amazon:\s*[\d.]+\/5★?)/i)
  
  if ((goodreadsMatch || amazonMatch) && (bookTitle || bookAuthor)) {
    const parts = []
    let remainingLine = formattedLine
    let keyIndex = 0

    // Handle Goodreads rating
    if (goodreadsMatch) {
      const beforeGoodreads = remainingLine.substring(0, remainingLine.indexOf(goodreadsMatch[1]))
      if (beforeGoodreads) {
        parts.push(<span key={`text-${keyIndex++}`}>{beforeGoodreads}</span>)
      }
      
      const ratingText = goodreadsMatch[1]
      parts.push(
        <a
          key={`goodreads-${keyIndex++}`}
          href={createSearchUrl('goodreads', bookTitle, bookAuthor)}
          target="_blank"
          rel="noopener noreferrer"
          className="rating-link"
          aria-label={`Search for ${bookTitle} on Goodreads`}
        >
          {ratingText}
        </a>
      )
      
      remainingLine = remainingLine.substring(remainingLine.indexOf(goodreadsMatch[1]) + ratingText.length)
    }

    // Handle Amazon rating
    if (amazonMatch) {
      const beforeAmazon = remainingLine.substring(0, remainingLine.indexOf(amazonMatch[1]))
      if (beforeAmazon) {
        parts.push(<span key={`text-${keyIndex++}`}>{beforeAmazon}</span>)
      }
      
      const ratingText = amazonMatch[1]
      parts.push(
        <a
          key={`amazon-${keyIndex++}`}
          href={createSearchUrl('amazon', bookTitle, bookAuthor)}
          target="_blank"
          rel="noopener noreferrer"
          className="rating-link"
          aria-label={`Search for ${bookTitle} on Amazon`}
        >
          {ratingText}
        </a>
      )
      
      remainingLine = remainingLine.substring(remainingLine.indexOf(amazonMatch[1]) + ratingText.length)
    }

    // Add any remaining text
    if (remainingLine) {
      parts.push(<span key={`text-${keyIndex++}`}>{remainingLine}</span>)
    }

    return parts.length > 1 ? parts : formattedLine
  }

  return formattedLine
}

/**
 * Parses recommendations text into structured book data
 */
export function parseRecommendations(text) {
  if (!text) return []

  const lines = text.split('\n')
  const books = []
  let currentBook = null
  let blurbStarted = false
  let blurbLines = []

  lines.forEach((line) => {
    const trimmedLine = line.trim()
    
    // Skip empty lines
    if (!trimmedLine) {
      // Empty line might indicate end of blurb or separation
      if (blurbStarted && blurbLines.length > 0) {
        // Continue collecting blurb (empty lines are part of paragraph breaks)
        blurbLines.push('')
      }
      return
    }
    
    // Clean markdown formatting
    const cleanedLine = cleanMarkdown(trimmedLine)
    
    // Don't replace stars here - only in rating displays
    let formattedLine = cleanedLine
    
    // Check if line is a numbered list item (starts with number followed by period)
    const isNumberedItem = /^\d+\./.test(formattedLine)
    
    // Check if this line starts the blurb section - multiple patterns to match
    const isBlurbStart = /^[-•]\s*[Bb]lurb\s*:?\s*/i.test(formattedLine) || 
                         /^[Bb]lurb\s*:?\s*/i.test(formattedLine) ||
                         /^-\s*[Bb]lurb/i.test(formattedLine)
    
    // Check if line looks like part of a blurb (long text without rating keywords)
    const looksLikeBlurbContent = formattedLine.length > 80 && 
                                   !formattedLine.match(/Goodreads:|Amazon:|rating|^\d+\./i) &&
                                   !formattedLine.match(/^[-•]\s*(Goodreads|Amazon)/i)
    
    if (isNumberedItem) {
      // Save previous book if it exists
      if (currentBook) {
        // Add accumulated blurb if any
        if (blurbLines.length > 0) {
          currentBook.blurb = blurbLines.join('\n\n').trim()
        }
        books.push(currentBook)
      }
      
      // Start a new book
      const bookInfo = extractBookInfo(formattedLine)
      currentBook = {
        title: bookInfo.title,
        author: bookInfo.author,
        formattedTitle: formattedLine,
        details: [],
        blurb: ''
      }
      blurbStarted = false
      blurbLines = []
    } else if (currentBook) {
      if (isBlurbStart) {
        // Blurb section starts - extract text after "Blurb:" or "Blurb"
        blurbStarted = true
        let blurbText = formattedLine
          .replace(/^[-•]\s*[Bb]lurb\s*:?\s*/i, '')
          .replace(/^[Bb]lurb\s*:?\s*/i, '')
        // Remove surrounding quotes (both single and double)
        blurbText = blurbText.replace(/^["'](.*)["']$/g, '$1')
        // Remove quotes at start or end
        blurbText = blurbText.replace(/^["']+|["']+$/g, '')
        blurbText = blurbText.trim()
        if (blurbText) {
          blurbLines.push(blurbText)
        }
      } else if (blurbStarted) {
        // Continue collecting blurb lines
        // Stop if we hit the next numbered item or a detail line that looks like ratings
        if (/^\d+\./.test(formattedLine) || formattedLine.match(/^[-•]\s*(Goodreads|Amazon)/i)) {
          // End of blurb, start of next book or detail
          blurbStarted = false
          currentBook.details.push(formattedLine)
        } else {
          // Clean up dashes, bullets, and quotes from blurb lines
          let cleanedLine = formattedLine
          // Remove leading dashes/bullets
          cleanedLine = cleanedLine.replace(/^[-•]\s+/, '')
          // Remove surrounding quotes (both single and double)
          cleanedLine = cleanedLine.replace(/^["'](.*)["']$/g, '$1')
          // Remove quotes at start or end (handles cases where quotes wrap the text)
          cleanedLine = cleanedLine.replace(/^["']+|["']+$/g, '')
          blurbLines.push(cleanedLine.trim())
        }
      } else {
        // This is part of the current book's details (ratings, explanation, etc.)
        // If we already have at least 2 detail lines (ratings + explanation), 
        // and this line looks like blurb content, treat it as blurb
        if (looksLikeBlurbContent && currentBook.details.length >= 2 && !blurbStarted) {
          // Likely a blurb if we have ratings and explanation already
          blurbStarted = true
          // Clean up dashes, bullets, and quotes from blurb lines
          let cleanedLine = formattedLine
          // Remove leading dashes/bullets
          cleanedLine = cleanedLine.replace(/^[-•]\s+/, '')
          // Remove surrounding quotes (both single and double)
          cleanedLine = cleanedLine.replace(/^["'](.*)["']$/g, '$1')
          // Remove quotes at start or end (handles cases where quotes wrap the text)
          cleanedLine = cleanedLine.replace(/^["']+|["']+$/g, '')
          blurbLines.push(cleanedLine.trim())
        } else {
          // Remove leading dash/bullet from explanation lines
          const cleanedDetail = formattedLine.replace(/^[-•]\s+/, '').trim()
          currentBook.details.push(cleanedDetail)
        }
      }
    }
  })

  // Don't forget the last book
  if (currentBook) {
    // Add accumulated blurb if any
    if (blurbLines.length > 0) {
      currentBook.blurb = blurbLines.join('\n\n').trim()
    }
    books.push(currentBook)
  }

  return books
}

// Export formatRatingLine for use in components
export { formatRatingLine }
