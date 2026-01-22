/**
 * RecommendationsDisplay Component
 * 
 * Displays the formatted book recommendations with expand/collapse functionality.
 * Updates in real-time as streaming content arrives.
 * 
 * @param {string} recommendations - Recommendations text to display
 * @param {Array<string>} selectedTags - Currently selected tags for filtering
 * @param {boolean} loading - Whether recommendations are currently loading/streaming
 */

import { useMemo, memo } from 'react'
import BookItem from './BookItem'
import { parseRecommendations } from '../utils/recommendationFormatter'

function RecommendationsDisplay({ recommendations, selectedTags, loading }) {
  // Memoize expensive parsing operation
  const books = useMemo(
    () => parseRecommendations(recommendations || ''),
    [recommendations]
  )

  if (!recommendations && !loading) return null

  return (
    <div className="recommendations">
      <h2>Recommended Books:</h2>
      
      {selectedTags.length > 0 && (
        <div className="filter-info">
          Filtered by: {selectedTags.join(', ')}
        </div>
      )}
      
      {loading && recommendations && (
        <div className="streaming-indicator">
          <span className="streaming-dot"></span>
          <span>Generating recommendations...</span>
        </div>
      )}
      
      <div className="recommendations-content">
        {books.length > 0 ? (
          books.map((book, index) => (
            <BookItem
              key={`book-${index}-${book.title}`}
              book={book}
              bookIndex={index}
            />
          ))
        ) : loading && !recommendations ? (
          <div className="streaming-indicator">
            <span className="streaming-dot"></span>
            <span>Starting to generate recommendations...</span>
          </div>
        ) : null}
        
        {recommendations && loading && (
          <div className="streaming-indicator streaming-footer">
            <span className="streaming-dot"></span>
            <span>More recommendations coming...</span>
          </div>
        )}
      </div>
    </div>
  )
}

export default memo(RecommendationsDisplay, (prevProps, nextProps) => {
  return (
    prevProps.recommendations === nextProps.recommendations &&
    prevProps.selectedTags === nextProps.selectedTags &&
    prevProps.loading === nextProps.loading
  )
})
