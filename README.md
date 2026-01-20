# Book Recommendation Web App

A beautiful web application that recommends books based on your preferences using OpenAI's API.

## Features

- 📚 Get personalized book recommendations based on books you love
- 🎨 Modern, responsive UI built with React
- 🚀 Fast API backend using FastAPI
- 🤖 Powered by OpenAI GPT models

## Project Structure

```
book-reccomendation/
├── backend/          # Python FastAPI backend
│   ├── main.py      # Main API server
│   ├── requirements.txt
│   └── .env.example
└── frontend/         # React frontend
    ├── src/
    │   ├── App.jsx
    │   ├── App.css
    │   └── main.jsx
    └── package.json
```

## Setup Instructions

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Mac/Linux:
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file based on `.env.example`:
   ```bash
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

   The frontend will run on `http://localhost:3000`

## Usage

1. Make sure both backend and frontend servers are running
2. Open your browser and go to `http://localhost:3000`
3. Enter a book name you love in the search bar
4. Click "Get Recommendations" to see personalized book suggestions

## API Endpoint

The backend exposes a single endpoint:

- **POST** `/api/recommend`
  - Request body: `{ "book_name": "The Great Gatsby" }`
  - Response: `{ "recommendations": "1. Book title...\n2. Another book..." }`

## Technologies Used

### Backend
- **FastAPI**: Modern, fast web framework for building APIs
- **OpenAI**: GPT API for generating book recommendations
- **Uvicorn**: ASGI server for running FastAPI

### Frontend
- **React**: UI library
- **Vite**: Fast build tool and dev server
- **CSS3**: Modern styling with gradients and animations

## Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key (required)

## Notes

- Make sure to keep your `.env` file secure and never commit it to version control
- The app uses `gpt-4o-mini` by default for cost efficiency. You can change this in `backend/main.py` if needed
- The backend includes CORS configuration to allow requests from the React frontend
