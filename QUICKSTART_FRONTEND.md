# Quick Start - Running Frontend with Backend

This guide helps you start both the backend and frontend together.

## Prerequisites

- Python 3.10+ with backend dependencies installed
- Node.js 18+ 
- Microphone access for audio recording

## Step 1: Start the Backend

Open a terminal and run:

```powershell
cd backend
python -m app.main
```

You should see:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

Keep this terminal open. The backend is now running at `http://localhost:8000`

You can verify it's working by visiting: http://localhost:8000/docs

## Step 2: Start the Frontend

Open a **NEW** terminal and run:

```powershell
cd frontend-design
npm run dev
```

You should see:
```
  VITE v6.3.5  ready in XXX ms

  ➜  Local:   http://localhost:5173/
```

## Step 3: Use the App

1. Open http://localhost:5173 in your browser
2. Select a Surah (e.g., Al-Fatihah) and Ayah number
3. Click "Start Recording"
4. Grant microphone permission if asked
5. Recite the ayah (max 12 seconds)
6. Click "Stop Recording"
7. Click "Analyze Recitation"
8. View your results with tajweed feedback!

## Troubleshooting

**Backend not starting?**
- Make sure you're in the `backend` directory
- Ensure Python dependencies are installed: `pip install -r requirements.txt`
- Check if port 8000 is already in use

**Frontend not starting?**
- Make sure you're in the `frontend-design` directory  
- Run `npm install` if you haven't already
- Check if port 5173 is already in use

**Can't connect to backend?**
- Verify backend is running at http://localhost:8000
- Check the frontend `.env` file has `VITE_API_BASE_URL=http://localhost:8000`

**Microphone not working?**
- Check browser permissions (click lock icon in address bar)
- Try using Chrome or Edge (best MediaRecorder support)
- Make sure no other app is using the microphone

## What's Happening

When you record and analyze:

1. **Frontend** captures audio using browser's MediaRecorder API
2. **Frontend** sends audio file to `POST /api/v1/recordings/analyze`
3. **Backend** normalizes audio to 16kHz WAV
4. **Backend** runs Whisper ASR to transcribe Arabic
5. **Backend** matches transcription to Quran verses
6. **Backend** performs tajweed rule checking
7. **Backend** returns errors, score, and recommendations
8. **Frontend** displays results beautifully!

Enjoy using the Qari App! 🕌
