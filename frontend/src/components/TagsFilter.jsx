/**
 * TagsFilter Component
 * 
 * Displays available tags as clickable chips and allows filtering by tags.
 * 
 * @param {Array<string>} availableTags - List of available tags
 * @param {Array<string>} selectedTags - List of currently selected tags
 * @param {boolean} loading - Loading state
 * @param {boolean} loadingTags - Tags loading state
 * @param {boolean} hasRecommendations - Whether recommendations are loaded
 * @param {Function} onTagToggle - Handler for tag toggle
 */

function TagsFilter({ 
  availableTags, 
  selectedTags, 
  loading, 
  loadingTags, 
  hasRecommendations,
  onTagToggle 
}) {
  // Don't render if no recommendations, tags, or loading state
  if (!hasRecommendations && !loadingTags && availableTags.length === 0) {
    return null
  }

  return (
    <div className="tags-section">
      <div className="tags-header">
        <h3>Filter by tags:</h3>
        {loadingTags && (
          <span className="tags-loading">Loading tags...</span>
        )}
        {!loadingTags && availableTags.length === 0 && hasRecommendations && (
          <span className="tags-loading">Tags will appear here after your search</span>
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
