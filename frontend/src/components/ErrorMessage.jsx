/**
 * ErrorMessage Component
 * 
 * Displays error messages to the user.
 * 
 * @param {string} error - Error message to display
 */

function ErrorMessage({ error }) {
  if (!error) return null

  return (
    <div className="error-message" role="alert">
      <span aria-hidden="true">⚠️</span>
      <span>{error}</span>
    </div>
  )
}

export default ErrorMessage
