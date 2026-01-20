/**
 * useTags Hook
 * 
 * Custom hook for managing tags state and fetching tags.
 * 
 * @returns {Object} - Tags state and functions
 */

import { useState, useCallback } from 'react'

const TAGS_ENDPOINT = '/api/tags'
const REQUEST_TIMEOUT = 30000 // 30 seconds
const MIN_BOOK_NAME_LENGTH_FOR_TAGS = 3

export function useTags() {
  const [availableTags, setAvailableTags] = useState([])
  const [selectedTags, setSelectedTags] = useState([])
  const [loadingTags, setLoadingTags] = useState(false)

  /**
   * Fetches tags for a book/author
   */
  const fetchTags = useCallback(async (bookName) => {
    const trimmedInput = bookName.trim()
    
    if (!trimmedInput || trimmedInput.length < MIN_BOOK_NAME_LENGTH_FOR_TAGS) {
      setAvailableTags([])
      setLoadingTags(false)
      return
    }

    setLoadingTags(true)

    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT)

      const response = await fetch(TAGS_ENDPOINT, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ book_name: trimmedInput }),
        signal: controller.signal,
      })

      clearTimeout(timeoutId)

      if (!response.ok) {
        setAvailableTags([])
        setLoadingTags(false)
        return
      }

      const data = await response.json()
      
      if (data && data.tags && Array.isArray(data.tags) && data.tags.length > 0) {
        // Validate tag content (basic security check)
        const validTags = data.tags
          .filter(tag => typeof tag === 'string' && tag.length <= 50)
          .slice(0, 20) // Limit to 20 tags
        setAvailableTags(validTags)
      } else {
        setAvailableTags([])
      }
    } catch (err) {
      if (err.name !== 'AbortError') {
        setAvailableTags([])
      }
    } finally {
      setLoadingTags(false)
    }
  }, [])

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

  return {
    availableTags,
    selectedTags,
    loadingTags,
    fetchTags,
    toggleTag,
    clearSelectedTags,
    clearAvailableTags,
    setSelectedTags
  }
}
