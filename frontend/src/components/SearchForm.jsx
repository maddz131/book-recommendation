/**
 * SearchForm Component
 * 
 * Provides the search input and submit button for book recommendations.
 * 
 * @param {string} bookName - Current book name value
 * @param {boolean} loading - Loading state
 * @param {number} maxLength - Maximum input length
 * @param {Function} onInputChange - Handler for input changes
 * @param {Function} onSubmit - Handler for form submission
 */

function SearchForm({ bookName, loading, maxLength, onInputChange, onSubmit }) {
  return (
    <form onSubmit={onSubmit} className="search-form" noValidate>
      <div className="search-container">
        <input
          type="text"
          value={bookName}
          onChange={onInputChange}
          placeholder="Enter a book you love..."
          className="search-input"
          disabled={loading}
          maxLength={maxLength}
          aria-label="Book name input"
          aria-required="true"
        />
        <button 
          type="submit" 
          className="search-button"
          disabled={loading}
          aria-label="Get book recommendations"
        >
          {loading ? 'Searching...' : 'Get Recommendations'}
        </button>
      </div>
      
      {/* Character count indicator */}
      {bookName.length > maxLength * 0.8 && (
        <div className="char-count">
          {bookName.length} / {maxLength}
        </div>
      )}
    </form>
  )
}

export default SearchForm
