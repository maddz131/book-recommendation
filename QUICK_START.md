# Quick Start Guide

## 🚀 Fastest Way to Run

### 1. Add Your OpenAI API Key

**IMPORTANT:** Before running, you need to add your OpenAI API key.

1. Open: `backend\.env`
2. Replace `your_openai_api_key_here` with your actual API key
3. Get your API key from: https://platform.openai.com/api-keys

### 2. Run the Application

**Option A: Using Batch Files (Easiest)**

1. **Double-click** `run-backend.bat` - This starts the backend server
2. **Double-click** `run-frontend.bat` - This starts the frontend server
3. **Open your browser** and go to: `http://localhost:3000`

**Option B: Using Command Line**

**Terminal 1 (Backend):**
```powershell
cd C:\PersonalDevProjects\book-reccomendation\backend
python main.py
```

**Terminal 2 (Frontend):**
```powershell
cd C:\PersonalDevProjects\book-reccomendation\frontend
npm run dev
```

**Browser:**
```
http://localhost:3000
```

### 3. Test It!

1. Type a book name (e.g., "The Great Gatsby")
2. Click "Get Recommendations"
3. Wait for AI-powered book suggestions! 📚

## Troubleshooting

- **Backend won't start?** Make sure you added your OpenAI API key to `backend\.env`
- **Port already in use?** Close other apps using ports 8000 or 3000
- **Need help?** See `TESTING_GUIDE.md` for detailed instructions
