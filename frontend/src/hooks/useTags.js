/**
 * useTags Hook
 * 
 * Custom hook for managing tags state.
 * Tags are received from the recommendation stream, not via separate API calls.
 * 
 * @returns {Object} - Tags state and functions
 */

import { useState, useCallback } from 'react'

export function useTags() {
  const [availableTags, setAvailableTags] = useState([])
  const [selectedTags, setSelectedTags] = useState([])

  /**
   * Toggles a tag in the selected tags list
   */
  const toggleTag = useCallback((tag) => {
    setSelectedTags(prev => {
      return prev.includes(tag)
        ? prev.filter(t => t !== tag)
        : [...prev, tag]
    })
  }, [])

  /**
   * Clears all selected tags
   */
  const clearSelectedTags = useCallback(() => {
    setSelectedTags([])
  }, [])

  /**
   * Clears available tags
   */
  const clearAvailableTags = useCallback(() => {
    setAvailableTags([])
  }, [])

  /**
   * Sets available tags directly (used when tags come from stream)
   */
  const setTagsFromStream = useCallback((tags) => {
    // Validate tag content (basic security check)
    const validTags = Array.isArray(tags)
      ? tags
          .filter(tag => typeof tag === 'string' && tag.length <= 50)
          .slice(0, 20) // Limit to 20 tags
      : []
    setAvailableTags(validTags)
  }, [])

  return {
    availableTags,
    selectedTags,
    loadingTags: false, // Tags come from stream, no separate loading state needed
    toggleTag,
    clearSelectedTags,
    clearAvailableTags,
    setTagsFromStream
  }
}
