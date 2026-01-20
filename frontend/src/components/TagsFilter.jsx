/**
 * TagsFilter Component
 * 
 * Displays available tags as clickable chips and allows filtering by tags.
 * Tags are received from the recommendation stream.
 * 
 * @param {Array<string>} availableTags - List of available tags
 * @param {Array<string>} selectedTags - List of currently selected tags
 * @param {boolean} loading - Loading state (includes tags since they come from stream)
 * @param {boolean} hasRecommendations - Whether recommendations are loaded
 * @param {Function} onTagToggle - Handler for tag toggle
 */

function TagsFilter({ 
  availableTags, 
  selectedTags, 
  loading, 
  hasRecommendations,
  onTagToggle 
}) {
  // Don't render if no recommendations and no tags
  if (!hasRecommendations && availableTags.length === 0) {
    return null
  }

  return (
    <div className="tags-section">
      <div className="tags-header">
        <h3>Filter by tags:</h3>
        {loading && availableTags.length === 0 && (
          <span className="tags-loading">Loading tags...</span>
        )}
        {!loading && availableTags.length === 0 && hasRecommendations && (
          <span className="tags-loading">No tags available for this search</span>
        )}
      </div>
      
      {availableTags.length > 0 && (
        <div className="tags-container">
          {availableTags.map((tag) => {
            const isSelected = selectedTags.includes(tag)
            return (
              <button
                key={tag}
                type="button"
                className={`tag-chip ${isSelected ? 'tag-chip-selected' : ''}`}
                onClick={() => onTagToggle(tag)}
                disabled={loading}
                aria-label={`Filter by ${tag} tag`}
                aria-pressed={isSelected}
              >
                {tag}
              </button>
            )
          })}
        </div>
      )}
      
      {selectedTags.length > 0 && (
        <div className="selected-tags-info">
          <span>
            {selectedTags.length} tag{selectedTags.length !== 1 ? 's' : ''} selected
            {loading && ' - Updating...'}
          </span>
        </div>
      )}
    </div>
  )
}

export default TagsFilter
