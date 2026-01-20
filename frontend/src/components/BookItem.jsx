/**
 * BookItem Component
 * 
 * Displays a single book recommendation with expand/collapse functionality
 * to show the book's blurb.
 * 
 * @param {Object} book - Book data object with blurb included
 * @param {number} bookIndex - Index of the book in the list
 */

import { useState, useCallback } from 'react'
import './BookItem.css'
import { extractRatings, formatRatingLine } from '../utils/recommendationFormatter'

function BookItem({ book, bookIndex }) {
  const [isExpanded, setIsExpanded] = useState(false)

  /**
   * Handles expand/collapse toggle
   */
  const handleToggle = useCallback(() => {
    setIsExpanded(prev => !prev)
  }, [])

  /**
   * Parse blurb and truncate to a few lines for preview
   */
  const getBlurbContent = useCallback(() => {
    if (!book.blurb) return { previewText: '', fullText: '', hasMore: false }
    
    const fullText = book.blurb.trim()
    const lines = fullText.split('\n').filter(line => line.trim().length > 0)
    
    // Show first 2-3 lines for preview
    const previewLineCount = 3
    const previewLines = lines.slice(0, previewLineCount)
    const previewText = previewLines.join(' ').trim()
    
    // Check if there's more content
    const hasMore = lines.length > previewLineCount || 
                    fullText.length > previewText.length
    
    return {
      previewText,
      fullText,
      hasMore
    }
  }, [book.blurb])

  const { previewText, fullText, hasMore } = getBlurbContent()

  // Extract ratings from details
  const ratings = extractRatings(book.details, book.title, book.author)
  
  // Filter out rating lines from details (they'll be shown inline)
  // Match rating patterns with or without dashes/bullets, standalone or combined
  const nonRatingDetails = book.details.filter(detail => {
    const trimmedDetail = detail.trim()
    // Check for rating patterns: "Goodreads: X.XX/5" or "Amazon: X.XX/5" 
    // with optional leading dashes/bullets and optional trailing stars/star
    const isRatingLine = trimmedDetail.match(/^[-•]?\s*(Goodreads|Amazon):\s*[\d.]+\/5/i) ||
                         trimmedDetail.match(/^(Goodreads|Amazon):\s*[\d.]+\/5/i) ||
                         // Also match combined rating lines like "Goodreads: X.XX/5 | Amazon: X.XX/5"
                         trimmedDetail.match(/^(Goodreads|Amazon):\s*[\d.]+\/5\s*[|]\s*(Amazon|Goodreads):\s*[\d.]+\/5/i)
    return !isRatingLine
  })

  return (
    <div className="book-item-container">
      {/* Book Title with Inline Ratings */}
      <div className="recommendation-item">
        <span className="recommendation-title-text">{book.formattedTitle}</span>
        {(ratings.goodreads || ratings.amazon) && (
          <span className="recommendation-ratings">
            {ratings.goodreads && (
              <a
                href={ratings.goodreads.url}
                target="_blank"
                rel="noopener noreferrer"
                className="rating-link inline-rating"
                aria-label={`Search for ${book.title} on Goodreads`}
              >
                {ratings.goodreads.display}
              </a>
            )}
            {ratings.goodreads && ratings.amazon && (
              <span className="rating-separator"> | </span>
            )}
            {ratings.amazon && (
              <a
                href={ratings.amazon.url}
                target="_blank"
                rel="noopener noreferrer"
                className="rating-link inline-rating"
                aria-label={`Search for ${book.title} on Amazon`}
              >
                {ratings.amazon.display}
              </a>
            )}
          </span>
        )}
      </div>

      {/* Book Details (explanations, etc. - ratings excluded) */}
      {nonRatingDetails.map((detail, index) => (
        <p
          key={`detail-${bookIndex}-${index}`}
          className="recommendation-text"
        >
          {formatRatingLine(detail, book.title, book.author)}
        </p>
      ))}

      {/* Blurb Content - Always visible with preview */}
      {book.blurb && (
        <div className="blurb-container">
          <div className="blurb-content">
            {/* Preview text (always shown) */}
            <div className="blurb-preview">
              {isExpanded ? (
                // Full blurb with paragraphs
                fullText.split('\n\n').map((paragraph, index) => (
                  paragraph.trim() && (
                    <p 
                      key={`para-full-${index}`} 
                      className={`blurb-paragraph ${index >= 1 ? 'blurb-paragraph-expanded' : ''}`}
                      style={{ animationDelay: `${Math.max(0, index - 1) * 0.1}s` }}
                    >
                      {paragraph.trim()}
                    </p>
                  )
                ))
              ) : (
                // Preview: first few lines
                <p className="blurb-paragraph blurb-preview-text">
                  {previewText}
                  {hasMore && <span className="blurb-ellipsis">...</span>}
                </p>
              )}
            </div>
            
            {/* Show more/less button */}
            {hasMore && (
              <button
                type="button"
                className="blurb-toggle-button"
                onClick={handleToggle}
                aria-expanded={isExpanded}
                aria-label={isExpanded ? 'Show less' : 'Show more'}
              >
                {isExpanded ? 'Show less' : 'Show more'}
                <span className={`blurb-toggle-icon ${isExpanded ? 'expanded' : ''}`} aria-hidden="true">
                  ▼
                </span>
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default BookItem
