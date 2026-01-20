# Testing Guide - Book Recommendation App

This guide will walk you through setting up and testing the application.

## Prerequisites Check ✅

- ✅ Python 3.14.0 installed
- ✅ Node.js v24.11.1 installed
- ✅ npm 11.6.2 installed
- ✅ Backend dependencies installed
- ✅ Frontend dependencies installed

## Step-by-Step Testing Instructions

### 1. Set Up OpenAI API Key

**IMPORTANT:** You need an OpenAI API key to test the application.

1. Navigate to the backend directory:
   ```powershell
   cd C:\PersonalDevProjects\book-reccomendation\backend
   ```

2. Create a `.env` file (if it doesn't exist):
   ```powershell
   Copy-Item .env.example .env
   ```

3. Edit the `.env` file and add your OpenAI API key:
   ```
   OPENAI_API_KEY=sk-your-actual-api-key-here
   ```

   **How to get an OpenAI API key:**
   - Go to https://platform.openai.com/api-keys
   - Sign in or create an account
   - Click "Create new secret key"
   - Copy the key and paste it in your `.env` file

### 2. Start the Backend Server

Open a **new PowerShell/Command Prompt window**:

```powershell
cd C:\PersonalDevProjects\book-reccomendation\backend
python main.py
```

**Expected output:**
```
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

✅ **Test the backend is running:**
Open your browser and go to: `http://localhost:8000`

You should see:
```json
{"message": "Book Recommendation API is running"}
```

### 3. Start the Frontend Server

Open a **second PowerShell/Command Prompt window**:

```powershell
cd C:\PersonalDevProjects\book-reccomendation\frontend
npm run dev
```

**Expected output:**
```
  VITE v5.0.8  ready in xxx ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: use --host to expose
```

### 4. Test the Application

1. **Open your browser** and navigate to: `http://localhost:3000`

2. **You should see:**
   - A beautiful gradient background
   - A header saying "📚 Book Recommendations"
   - A search input field
   - A "Get Recommendations" button

3. **Test the search functionality:**
   - Enter a book name (e.g., "The Great Gatsby", "1984", "Harry Potter")
   - Click "Get Recommendations"
   - Wait a few seconds for the API to respond
   - You should see a list of recommended books appear below

### 5. Testing Different Scenarios

#### ✅ **Happy Path:**
- Enter: `"The Great Gatsby"`
- Expected: A numbered list of 5-8 book recommendations with explanations

#### ✅ **Empty Input:**
- Click search without entering anything
- Expected: Error message "Please enter a book name"

#### ✅ **Invalid API Key:**
- If you see an error about API key, check your `.env` file
- Make sure the key is correct and starts with `sk-`

### 6. Testing the API Directly (Optional)

You can test the backend API directly using curl or Postman:

**Using PowerShell:**
```powershell
$body = @{book_name = "The Great Gatsby"} | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/api/recommend" -Method Post -Body $body -ContentType "application/json"
```

**Using curl (if installed):**
```bash
curl -X POST "http://localhost:8000/api/recommend" -H "Content-Type: application/json" -d "{\"book_name\": \"The Great Gatsby\"}"
```

## Troubleshooting

### Backend won't start
- ✅ Check that port 8000 is not already in use
- ✅ Verify `.env` file exists and has the correct API key
- ✅ Make sure all dependencies are installed: `pip install -r requirements.txt`

### Frontend won't start
- ✅ Check that port 3000 is not already in use
- ✅ Verify all dependencies are installed: `npm install`
- ✅ Make sure you're in the frontend directory

### API returns errors
- ✅ Verify your OpenAI API key is correct in `.env`
- ✅ Check that you have credits in your OpenAI account
- ✅ Look at the backend terminal for error messages

### CORS errors
- ✅ Make sure both servers are running
- ✅ Backend should be on `http://localhost:8000`
- ✅ Frontend should be on `http://localhost:3000`

## Expected Results

When working correctly, you should see:

1. **Backend running** on `http://localhost:8000` ✅
2. **Frontend running** on `http://localhost:3000` ✅
3. **Beautiful UI** with gradient background ✅
4. **Book recommendations** appear when you search ✅
5. **Loading states** show while fetching ✅
6. **Error messages** display appropriately ✅

## Quick Start Commands Summary

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

Happy testing! 🎉
