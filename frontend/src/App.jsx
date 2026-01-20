/**
 * Book Recommendation App - Main Component
 * 
 * Main application component that orchestrates book recommendations.
 * Uses custom hooks and components for better code organization.
 */

import { useState, useCallback, useEffect } from 'react'
import './App.css'
import Header from './components/Header'
import SearchForm from './components/SearchForm'
import TagsFilter from './components/TagsFilter'
import ErrorMessage from './components/ErrorMessage'
import RecommendationsDisplay from './components/RecommendationsDisplay'
import { useBookRecommendations } from './hooks/useBookRecommendations'
import { useTags } from './hooks/useTags'

// Configuration constants
const MAX_BOOK_NAME_LENGTH = 200

function App() {
  // State management
  const [bookName, setBookName] = useState('')

  // Custom hooks for recommendations and tags
  const tagsHook = useTags()
  const recommendations = useBookRecommendations()
  
  // Update available tags when tags come from stream
  useEffect(() => {
    if (recommendations.tagsFromStream && recommendations.tagsFromStream.length > 0) {
      // Only update if tags are different to avoid unnecessary re-renders
      const currentTags = tagsHook.availableTags.map(t => t.toLowerCase()).sort().join(',')
      const newTags = recommendations.tagsFromStream.map(t => t.toLowerCase()).sort().join(',')
      if (currentTags !== newTags) {
        tagsHook.setTagsFromStream(recommendations.tagsFromStream)
      }
    }
  }, [recommendations.tagsFromStream, tagsHook.availableTags, tagsHook.setTagsFromStream])

  /**
   * Handles input changes with validation
   */
  const handleInputChange = useCallback((e) => {
    const value = e.target.value
    
    // Enforce maximum length
    if (value.length > MAX_BOOK_NAME_LENGTH) {
      return
    }
    
    setBookName(value)
    
    // Clear error when user starts typing
    if (recommendations.error) {
      recommendations.setError('')
    }
    
    // Clear recommendations when input changes
    if (recommendations.recommendations) {
      recommendations.clearRecommendations()
    }
    
    // Clear selected tags if input is significantly different
    const isDifferentBook = value.trim().toLowerCase() !== recommendations.searchedBookName.toLowerCase()
    if (isDifferentBook && tagsHook.selectedTags.length > 0) {
      tagsHook.clearSelectedTags()
    }
  }, [recommendations, tagsHook.selectedTags.length, tagsHook.clearSelectedTags])

  /**
   * Handles form submission to get book recommendations
   */
  const handleSubmit = useCallback(async (e) => {
    e.preventDefault()
    
    const trimmedBookName = bookName.trim()
    if (!trimmedBookName) {
      recommendations.setError('Please enter a book name')
      return
    }

    if (trimmedBookName.length > MAX_BOOK_NAME_LENGTH) {
      recommendations.setError(`Book name must be less than ${MAX_BOOK_NAME_LENGTH} characters`)
      return
    }

    // Clear recommendations when starting a new search
    recommendations.clearRecommendations()
    
    // Clear tags when starting a completely new search
    if (trimmedBookName.toLowerCase() !== recommendations.searchedBookName.toLowerCase()) {
      tagsHook.clearAvailableTags()
      tagsHook.clearSelectedTags()
    }

    // Fetch recommendations
    await recommendations.fetchRecommendations(trimmedBookName, tagsHook.selectedTags)
  }, [bookName, tagsHook.selectedTags, recommendations, tagsHook])

  /**
   * Handles tag checkbox toggle and re-fetches recommendations
   */
  const handleTagToggle = useCallback((tag) => {
    // Calculate new tags state before updating
    const newTags = tagsHook.selectedTags.includes(tag)
      ? tagsHook.selectedTags.filter(t => t !== tag)
      : [...tagsHook.selectedTags, tag]
    
    // Update tags state
    tagsHook.toggleTag(tag)
    
    // Re-fetch recommendations when tags change
    if (recommendations.recommendations && recommendations.searchedBookName) {
      const trimmedBookName = recommendations.searchedBookName.trim()
      if (trimmedBookName) {
        // Use requestAnimationFrame to ensure state update completes
        requestAnimationFrame(() => {
          recommendations.fetchRecommendations(trimmedBookName, newTags)
        })
      }
    }
  }, [recommendations, tagsHook])

  return (
    <div className="app">
      <div className="container">
        <Header />

        <SearchForm
          bookName={bookName}
          loading={recommendations.loading}
          maxLength={MAX_BOOK_NAME_LENGTH}
          onInputChange={handleInputChange}
          onSubmit={handleSubmit}
        />

        <TagsFilter
          availableTags={tagsHook.availableTags}
          selectedTags={tagsHook.selectedTags}
          loading={recommendations.loading}
          hasRecommendations={!!recommendations.recommendations}
          onTagToggle={handleTagToggle}
        />

        <ErrorMessage error={recommendations.error} />

              <RecommendationsDisplay
                recommendations={recommendations.recommendations}
                selectedTags={tagsHook.selectedTags}
                loading={recommendations.loading}
              />
      </div>
    </div>
  )
}

export default App
