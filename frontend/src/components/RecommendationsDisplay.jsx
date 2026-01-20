/**
 * RecommendationsDisplay Component
 * 
 * Displays the formatted book recommendations.
 * 
 * @param {string} recommendations - Recommendations text to display
 * @param {Array<string>} selectedTags - Currently selected tags for filtering
 * @param {Function} formatRecommendations - Function to format recommendations text
 */

function RecommendationsDisplay({ recommendations, selectedTags, formatRecommendations }) {
  if (!recommendations) return null

  return (
    <div className="recommendations">
      <h2>Recommended Books:</h2>
      
      {selectedTags.length > 0 && (
        <div className="filter-info">
          Filtered by: {selectedTags.join(', ')}
        </div>
      )}
      
      <div className="recommendations-content">
        {formatRecommendations(recommendations)}
      </div>
    </div>
  )
}

export default RecommendationsDisplay
