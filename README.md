# Qari App - Quran Recitation Analysis

A mobile-first application that records Quran recitations, analyzes them using ASR + forced alignment + tajweed checking (hybrid rule-based + ML), and provides precise feedback with correction audio.

## Features

- **Audio Recording**: Record recitations directly from the mobile app
- **ASR Transcription**: Automatic speech recognition using Whisper
- **Verse Detection**: Match transcription to Quran verses with high accuracy
- **Tajweed Analysis**: Detect common tajweed errors:
  - Letter substitutions (e.g., qaf to kaf)
  - Madd (elongation) errors
  - Ghunnah (nasalization) issues
  - Qalqalah (echo/bounce) errors
  - Missing words
- **Correction Audio**: Play correct pronunciation samples
- **Repetition Loop**: Practice specific errors until mastered
- **Progress Tracking**: Monitor improvement over time
- **Human Review**: Expert Qari validation for uncertain cases

## Tech Stack

### Backend
- **Framework**: Python 3.11, FastAPI
- **ML/AI**: OpenAI Whisper, WhisperX (forced alignment)
- **Audio Processing**: pydub, librosa, torchaudio
- **Database**: PostgreSQL + Redis
- **Storage**: S3-compatible object storage

### Mobile
- **Framework**: React Native (RN CLI)
- **Navigation**: React Navigation
- **State Management**: Zustand
- **Audio**: react-native-audio-recorder-player

### DevOps
- **Containerization**: Docker, Docker Compose
- **CI/CD**: GitHub Actions
- **Cloud**: AWS/GCP

## Project Structure

```
qari-app/
+-- mobile/                 # React Native app
¦   +-- src/
¦   ¦   +-- screens/       # App screens
¦   ¦   +-- components/    # Reusable components
¦   ¦   +-- services/      # API & utilities
¦   +-- package.json
+-- backend/
¦   +-- app/
¦   ¦   +-- main.py        # FastAPI entry point
¦   ¦   +-- routes/        # API endpoints
¦   ¦   +-- services/      # Business logic
¦   ¦   +-- models/        # ML model checkpoints
¦   +-- docker/
¦   +-- requirements.txt
¦   +-- docker-compose.yml
+-- docs/
¦   +-- api_spec.md
¦   +-- data_schema.csv
+-- infra/
    +-- terraform/
```

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js >= 18
- Python 3.11 (for local development)
- React Native development environment

### Backend Setup

1. **Clone and navigate to backend:**
   ```bash
   git clone https://github.com/Ammmaarrr/qari-app.git
   cd qari-app/backend
   ```

2. **Copy environment file:**
   ```bash
   cp .env.example .env
   ```

3. **Run with Docker:**
   ```bash
   docker compose up --build
   ```

4. **Verify it's running:**
   ```bash
   curl http://localhost:8000/health
   ```

5. **Access API docs:**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Mobile Setup

1. **Navigate to mobile directory:**
   ```bash
   cd qari-app/mobile
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Run on iOS:**
   ```bash
   cd ios && pod install && cd ..
   npx react-native run-ios
   ```

4. **Run on Android:**
   ```bash
   npx react-native run-android
   ```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| /health | GET | Health check |
| /api/v1/recordings/analyze | POST | Analyze recording |
| /api/v1/recordings/analyze/quick | POST | Quick analysis for repetition |
| /api/v1/correction/audio/{id} | GET | Get correction audio |
| /api/v1/feedback/review | POST | Submit human review |
| /api/v1/feedback/queue | GET | Get review queue |

See docs/api_spec.md for complete API documentation.

## Response Format

```json
{
  "matched_ayah": {
    "surah": 1,
    "ayah": 1,
    "confidence": 0.92
  },
  "errors": [
    {
      "type": "substituted_letter",
      "letter": "qaf",
      "confidence": 0.85,
      "suggestion": "Press back of tongue against soft palate",
      "correction_audio_url": "/api/v1/correction/audio/qa_01"
    }
  ],
  "overall_score": 0.78,
  "recommendation": "Focus on: letter pronunciation"
}
```

## Sprint Plan

### Sprint 0 (Setup) - COMPLETE
- [x] Repo skeleton
- [x] Docker Compose
- [x] FastAPI skeleton with mock response

### Sprint 1 (MVP ASR + Basic UI)
- [ ] Mobile UI recording
- [ ] Backend Whisper integration
- [ ] Verse detection

### Sprint 2 (Tajweed Checks)
- [ ] Rule-based detectors
- [ ] Error display UI
- [ ] Repetition loop

### Sprint 3-5 (Advanced Features)
- [ ] WhisperX integration
- [ ] ML classifiers
- [ ] Production deployment

## Security & Privacy

- User consent required before recording
- Audio encrypted at rest
- User identification via UUID only
- GDPR/CCPA compliance ready

## License

MIT License

---

**Built with love for the Muslim community**
