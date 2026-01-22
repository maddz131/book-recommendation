# Book Recommendation Web App

A modern web application that recommends books based on your preferences using OpenAI's API. Features real-time streaming recommendations, tag-based filtering, and official Goodreads blurbs.

## Features

- 📚 **Personalized Recommendations**: Get 5-8 book recommendations based on books you love
- ⚡ **Real-time Streaming**: See recommendations appear in real-time as they're generated
- 🏷️ **Tag-based Filtering**: Filter recommendations by genre, themes, and characteristics (e.g., romance, mafia, sci-fi)
- 📖 **Official Goodreads Blurbs**: View official book blurbs from Goodreads.com
- ⭐ **Ratings & Links**: See Goodreads and Amazon ratings with clickable links to search pages
- 🎨 **Modern UI**: Beautiful, responsive interface built with React
- 🔒 **Secure**: Input validation, error handling, and security best practices

  <img width="1666" height="978" alt="Screenshot 2026-01-19 190625" src="https://github.com/user-attachments/assets/63dc491b-086d-45fe-b4a4-1d7b7ed493c9" />


## Project Structure

```
book-reccomendation/
├── backend/                    # Python FastAPI backend
│   ├── main.py                # FastAPI app initialization and entry point
│   ├── config.py              # Configuration constants and environment setup
│   ├── models.py              # Pydantic request/response models
│   ├── routers/               # API endpoint routers
│   │   ├── __init__.py
│   │   ├── recommendations.py # /api/recommend endpoint with streaming
│   │   └── tags.py            # /api/tags endpoint
│   ├── services/              # Business logic services
│   │   ├── __init__.py
│   │   ├── openai_service.py  # OpenAI client initialization with connection pooling
│   │   ├── prompt_service.py  # Prompt building and sanitization utilities
│   │   ├── error_handler.py   # Centralized API error handling
│   │   ├── cache_service.py   # Caching service (in-memory + Redis support)
│   │   └── database_service.py # Database service for analytics (SQLite)
│   ├── requirements.txt       # Python dependencies
│   └── .env.example           # Example environment file
└── frontend/                  # React frontend
    ├── src/
    │   ├── App.jsx            # Main app component
    │   ├── components/        # Reusable React components
    │   │   ├── Header.jsx
    │   │   ├── SearchForm.jsx
    │   │   ├── TagsFilter.jsx
    │   │   ├── BookItem.jsx
    │   │   ├── RecommendationsDisplay.jsx
    │   │   └── ErrorMessage.jsx
    │   ├── hooks/             # Custom React hooks
    │   │   ├── useBookRecommendations.js
    │   │   └── useTags.js
    │   ├── utils/             # Utility functions
    │   │   └── recommendationFormatter.jsx
    │   └── App.css            # Styles
    └── package.json
```

## Setup Instructions

### Prerequisites

- Python 3.8+ (for backend)
- Node.js 16+ and npm (for frontend)
- OpenAI API key

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\Activate.ps1
   # On Mac/Linux:
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file:
   ```bash
   # On Windows:
   copy .env.example .env
   # On Mac/Linux:
   cp .env.example .env
   ```

5. Add your OpenAI API key to the `.env` file:
   ```
   OPENAI_API_KEY=your_actual_api_key_here
   ```

6. Run the backend server:
   ```bash
   python main.py
   # Or using uvicorn directly:
   uvicorn main:app --reload
   ```

   The backend will run on `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Run the development server:
   ```bash
   npm run dev
   ```

   The frontend will run on `http://localhost:5173` (Vite default port)

## Usage

1. Make sure both backend and frontend servers are running
2. Open your browser and go to `http://localhost:5173`
3. Enter a book name or author in the search bar
4. Click "Get Recommendations" or press Enter
5. Watch recommendations stream in real-time
6. Use the tag filters that appear to refine your results
7. Click on ratings to search Goodreads or Amazon
8. Expand blurbs to read the full official description

## API Endpoints

### POST `/api/recommend`

Get streaming book recommendations based on a book name and optional tags.

**Request:**
```json
{
  "book_name": "The Great Gatsby",
  "tags": ["classic", "literary fiction"]  // Optional
}
```

**Response:** Server-Sent Events (SSE) stream with:
- `{"tags": [...]}` - List of available tags (sent first)
- `{"chunk": "...", "text": "..."}` - Streaming recommendation chunks
- `{"done": true, "text": "..."}` - Final complete recommendations

**Example Response Format:**
```
1. Book Title by Author Name
   Goodreads: 4.5/5★ | Amazon: 4.7/5★
   Brief explanation of why this book is recommended...
   Blurb: Official Goodreads.com book blurb...
```

## Technologies Used

### Backend
- **FastAPI**: Modern, fast web framework for building APIs
- **OpenAI**: GPT API for generating book recommendations (supports gpt-4o-mini, gpt-5-nano, etc.)
- **Uvicorn**: ASGI server for running FastAPI
- **Pydantic**: Data validation and settings management
- **python-dotenv**: Environment variable management

### Frontend
- **React**: UI library with hooks for state management
- **Vite**: Fast build tool and dev server
- **CSS3**: Modern styling with gradients, animations, and responsive design

## Configuration

### Model Selection

The app uses `gpt-4o-mini` by default for cost efficiency. To use a different model, edit `backend/config.py`:

```python
OPENAI_MODEL = "gpt-4o-mini"  # Change to "gpt-5-nano" or other models
```

**Note:** For `gpt-5` models, you may need to increase `OPENAI_MAX_TOKENS` (e.g., 8000) since these models use tokens for internal reasoning before generating content.

### Token Limits

Adjust `OPENAI_MAX_TOKENS` in `backend/config.py` based on your needs:
- **gpt-4o-mini**: 2000 tokens (default)
- **gpt-5 models**: 8000+ tokens (recommended, as they use tokens for reasoning)

## Environment Variables

- `OPENAI_API_KEY` (required): Your OpenAI API key

## Security Features

- ✅ Input validation and sanitization
- ✅ Prompt injection protection
- ✅ CORS configuration
- ✅ Error handling without exposing internal details
- ✅ Environment variable protection
- ✅ XSS prevention in frontend

## Best Practices Implemented

- **Code Organization**: 
  - Modular React components and custom hooks (frontend)
  - Separation of concerns with routers, services, and models (backend)
  - Centralized error handling and configuration management
- **Error Handling**: Comprehensive error handling on both frontend and backend with centralized error handler service
- **Performance**: Real-time streaming for better UX, debounced inputs where appropriate
- **Accessibility**: ARIA labels and semantic HTML
- **Security**: Input validation, sanitization, and secure API key handling
- **Stateless**: Each request is independent with no memory of previous searches
- **Maintainability**: Clean architecture with single responsibility principle

## Troubleshooting

### Backend won't start
- Ensure your `.env` file exists in the `backend/` directory
- Verify your `OPENAI_API_KEY` is set correctly
- Check that all dependencies are installed

### No recommendations showing
- Check browser console for errors
- Verify backend is running on port 8000
- Check backend logs for API errors
- Ensure you're using a valid OpenAI model name

### Tags not appearing
- Tags are generated automatically with recommendations
- If tags don't appear, try a different book search
- Check backend logs for tag generation errors

## License

This project is open source and available for personal and commercial use.

## Performance Optimization

- **Implemented Optimizations**: See [OPTIMIZATION_SUMMARY.md](./OPTIMIZATION_SUMMARY.md) for details on all implemented performance improvements
- **Future Optimizations**: See [PERFORMANCE_OPTIMIZATION.md](./PERFORMANCE_OPTIMIZATION.md) for additional recommendations

### Quick Performance Features

- ✅ **Caching**: In-memory + Redis support (90%+ reduction in API calls)
- ✅ **Rate Limiting**: 10 requests/minute protection
- ✅ **Connection Pooling**: Better throughput for OpenAI API
- ✅ **Compression**: GZip middleware for bandwidth savings
- ✅ **Database Analytics**: SQLite for tracking popular searches
- ✅ **React Optimizations**: Memoization, code splitting, lazy loading
