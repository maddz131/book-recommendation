/**
 * useBookRecommendations Hook
 * 
 * Custom hook for managing book recommendations state and fetching recommendations.
 * Tags are now included in the recommendation stream.
 * 
 * @returns {Object} - Recommendations state and functions
 */

import { useState, useCallback } from 'react'

const API_ENDPOINT = '/api/recommend'

export function useBookRecommendations() {
  const [recommendations, setRecommendations] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [searchedBookName, setSearchedBookName] = useState('')
  const [tagsFromStream, setTagsFromStream] = useState([])

  /**
   * Fetches recommendations with given book name and tags using streaming
   */
  const fetchRecommendations = useCallback(async (bookName, tags = []) => {
    setLoading(true)
    setError('')
    setRecommendations('') // Clear previous recommendations
    setTagsFromStream([]) // Clear previous tags

    try {
      const controller = new AbortController()
      
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

      // Always try to read as a stream - FastAPI StreamingResponse sends SSE format
      // Even if content-type header is missing, try to read the body as a stream
      if (response.body) {
        // Handle streaming response
        const reader = response.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ''
        let lastReceivedText = '' // Track last received text in case done message is missed

        try {
          while (true) {
            const { done, value } = await reader.read()
            
            if (done) {
              // Process any remaining buffer before exiting
              if (buffer.trim()) {
                const lines = buffer.split('\n\n').filter(line => line.trim())
                for (const line of lines) {
                  if (line.startsWith('data: ')) {
                    try {
                      const data = JSON.parse(line.slice(6))
                      
                      if (data.error) {
                        setError(data.error)
                        setLoading(false)
                        return
                      }
                      
                      if (data.tags && Array.isArray(data.tags)) {
                        setTagsFromStream(data.tags)
                      }
                      
                      if (data.chunk || data.text) {
                        const newText = data.text || data.chunk
                        lastReceivedText = newText
                        setRecommendations(newText)
                      }
                      
                      if (data.done) {
                        if (data.text) {
                          setRecommendations(data.text)
                          lastReceivedText = data.text
                        }
                        setSearchedBookName(bookName)
                        setLoading(false)
                        return
                      }
                    } catch (parseError) {
                      // Skip malformed JSON
                    }
                  }
                }
              }
              break
            }

            // Decode chunk
            const chunkText = decoder.decode(value, { stream: true })
            buffer += chunkText
            
            // Process complete SSE messages (lines ending with \n\n)
            const messages = []
            let lastIndex = 0
            
            while (true) {
              const endIndex = buffer.indexOf('\n\n', lastIndex)
              if (endIndex === -1) {
                // No complete message found, keep remaining buffer from lastIndex
                buffer = buffer.slice(lastIndex)
                break
              }
              
              // Extract complete message (includes "data: " prefix)
              const message = buffer.slice(lastIndex, endIndex).trim()
              if (message) {
                messages.push(message)
              }
              lastIndex = endIndex + 2 // Skip the \n\n
            }
            
            // Process each complete SSE message
            for (const message of messages) {
              // SSE format: "data: {json}" or just "data: " followed by content
              if (message.startsWith('data: ')) {
                try {
                  const jsonStr = message.slice(6).trim() // Remove "data: " prefix
                  if (!jsonStr) continue // Skip empty data lines
                  
                  const data = JSON.parse(jsonStr)
                  
                  if (data.error) {
                    setError(data.error)
                    setLoading(false)
                    return
                  }
                  
                  // Handle tags sent first in stream
                  if (data.tags && Array.isArray(data.tags)) {
                    setTagsFromStream(data.tags)
                    // Continue processing stream for recommendations
                    continue
                  }
                  
                  if (data.chunk || data.text) {
                    // Update recommendations with accumulated text
                    const newText = data.text || data.chunk
                    lastReceivedText = newText // Track latest text
                    setRecommendations(newText)
                  }
                  
                  if (data.done) {
                    // Streaming complete - ensure final text is set
                    if (data.text) {
                      setRecommendations(data.text)
                      lastReceivedText = data.text
                    }
                    setSearchedBookName(bookName)
                    setLoading(false)
                    return
                  }
                } catch (parseError) {
                  // Skip malformed JSON - might be partial data
                  // Continue processing other messages
                }
              }
            }
          }
          
          // Ensure loading is set to false after stream completes
          // If we have accumulated text but no done message was received, ensure it's set
          if (lastReceivedText) {
            setRecommendations(prev => prev || lastReceivedText)
          }
          setSearchedBookName(bookName)
          setLoading(false)
        } finally {
          reader.releaseLock()
        }
      } else {
        // Backend should always return streaming response
        throw new Error('Unexpected response format from server')
      }
      
    } catch (err) {
      if (err.name === 'AbortError') {
        setError('Request was cancelled.')
      } else if (err.message) {
        setError(err.message)
      } else {
        setError('An error occurred while fetching recommendations. Please try again.')
      }
      setLoading(false)
    }
  }, [])

  const clearRecommendations = useCallback(() => {
    setRecommendations('')
  }, [])

  return {
    recommendations,
    loading,
    error,
    searchedBookName,
    tagsFromStream,
    fetchRecommendations,
    clearRecommendations,
    setError
  }
}
