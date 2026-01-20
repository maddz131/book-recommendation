/**
 * Recommendation Formatter Utility
 * 
 * Formats recommendations text into React elements with clickable rating links.
 * 
 * @param {string} text - The recommendations text from the API
 * @returns {Array} - Array of React elements to render
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
  const searchQuery = bookAuthor ? `${bookTitle} ${bookAuthor}` : bookTitle
  const encodedQuery = encodeURIComponent(searchQuery)
  
  if (domain === 'goodreads') {
    return `https://www.goodreads.com/search?q=${encodedQuery}`
  }
  return `https://www.amazon.com/s?k=${encodedQuery}&i=stripbooks`
}

/**
 * Formats a rating line with clickable links
 */
function formatRatingLine(line, bookTitle, bookAuthor) {
  // Replace "stars" with star symbol
  let formattedLine = line.replace(/\bstars\b/gi, '★').replace(/\bstar\b/gi, '★')
  
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
 * Formats recommendations text into React elements
 */
export function formatRecommendations(text) {
  if (!text) return []

  const lines = text.split('\n')
  const elements = []
  let currentBookIndex = 0
  let currentBookTitle = ''
  let currentBookAuthor = ''

  lines.forEach((line, index) => {
    const trimmedLine = line.trim()
    
    // Skip empty lines
    if (!trimmedLine) return
    
    // Clean markdown formatting
    const cleanedLine = cleanMarkdown(trimmedLine)
    
    // Replace "stars" with star symbol
    let formattedLine = cleanedLine.replace(/\bstars\b/gi, '★').replace(/\bstar\b/gi, '★')
    
    // Check if line is a numbered list item (starts with number followed by period)
    const isNumberedItem = /^\d+\./.test(formattedLine)
    
    if (isNumberedItem) {
      // Start a new book recommendation group
      currentBookIndex++
      const bookInfo = extractBookInfo(formattedLine)
      currentBookTitle = bookInfo.title
      currentBookAuthor = bookInfo.author
      
      elements.push(
        <p
          key={`book-${currentBookIndex}`}
          className="recommendation-item"
        >
          {formattedLine}
        </p>
      )
    } else {
      // This is part of the current book's details (ratings, explanation, etc.)
      const ratingContent = formatRatingLine(formattedLine, currentBookTitle, currentBookAuthor)
      
      elements.push(
        <p
          key={`detail-${index}`}
          className="recommendation-text"
        >
          {ratingContent}
        </p>
      )
    }
  })

  return elements
}
