/**
 * useBookRecommendations Hook
 * 
 * Custom hook for managing book recommendations state and fetching recommendations.
 * 
 * @param {Function} fetchTags - Function to fetch tags for a book
 * @returns {Object} - Recommendations state and functions
 */

import { useState, useCallback } from 'react'

const API_ENDPOINT = '/api/recommend'
const REQUEST_TIMEOUT = 30000 // 30 seconds

export function useBookRecommendations(fetchTags) {
  const [recommendations, setRecommendations] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [searchedBookName, setSearchedBookName] = useState('')

  /**
   * Fetches recommendations with given book name and tags
   */
  const fetchRecommendations = useCallback(async (bookName, tags = []) => {
    setLoading(true)
    setError('')

    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT)

      const response = await fetch(API_ENDPOINT, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          book_name: bookName,
          tags: tags
        }),
        signal: controller.signal,
      })

      clearTimeout(timeoutId)

      if (!response.ok) {
        let errorMessage = 'Failed to get recommendations'
        try {
          const errorData = await response.json()
          errorMessage = errorData.detail || errorMessage
        } catch (parseError) {
          errorMessage = response.statusText || errorMessage
        }
        
        if (response.status === 429) {
          errorMessage = 'Too many requests. Please wait a moment and try again.'
        } else if (response.status >= 500) {
          errorMessage = 'Server error. Please try again later.'
        }
        
        throw new Error(errorMessage)
      }

      const data = await response.json()
      
      if (!data || !data.recommendations) {
        throw new Error('Invalid response from server')
      }
      
      setRecommendations(data.recommendations)
      setSearchedBookName(bookName)
      
      // Fetch tags after successful recommendation search (only for initial search)
      if (tags.length === 0 && fetchTags) {
        fetchTags(bookName).catch(() => {
          // Silently handle errors - tags are optional
        })
      }
      
    } catch (err) {
      if (err.name === 'AbortError') {
        setError('Request timed out. Please try again.')
      } else if (err.message) {
        setError(err.message)
      } else {
        setError('An error occurred while fetching recommendations. Please try again.')
      }
    } finally {
      setLoading(false)
    }
  }, [fetchTags])

  const clearRecommendations = useCallback(() => {
    setRecommendations('')
  }, [])

  return {
    recommendations,
    loading,
    error,
    searchedBookName,
    fetchRecommendations,
    clearRecommendations,
    setError
  }
}
