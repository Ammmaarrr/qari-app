# Qari App API Specification

## Base URL
- Development: `http://localhost:8000`
- Production: `https://api.qari-app.com`

## Authentication
All endpoints except health checks require authentication via JWT token in the Authorization header:
```
Authorization: Bearer <token>
```

---

## Endpoints

### Health Check

#### GET /health
Health check for load balancers.

**Response:**
```json
{
  "status": "healthy",
  "service": "qari-app-api"
}
```

#### GET /ready
Readiness check - verifies all dependencies are available.

**Response:**
```json
{
  "status": "ready",
  "database": "connected",
  "redis": "connected",
  "models": "loaded"
}
```

---

### Recording Analysis

#### POST /api/v1/recordings/analyze

Analyze a Quran recitation recording.

**Request:**
- Content-Type: `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| user_id | string | Yes | User identifier (UUID) |
| surah | int | No | Surah number (1-114) |
| ayah | int | No | Ayah number |
| mode | string | No | Recording mode: "short" or "long" (default: "short") |
| audio_file | file | Yes | Audio file (WAV/MP3/M4A/OGG/WEBM) |

**Response (200 OK):**
```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "matched_ayah": {
    "surah": 1,
    "ayah": 1,
    "confidence": 0.92,
    "text": "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"
  },
  "errors": [
    {
      "type": "substituted_letter",
      "letter": "ق",
      "expected": "ق",
      "detected": "ك",
      "start_time": 0.56,
      "end_time": 0.68,
      "confidence": 0.85,
      "suggestion": "The letter 'ق' was pronounced as 'ك'. Press back of tongue against soft palate.",
      "correction_audio_url": "/api/v1/correction/audio/qa_01",
      "word_index": 2,
      "severity": "high"
    }
  ],
  "overall_score": 0.78,
  "recommendation": "Good effort. Focus on: letter pronunciation, elongation (madd)",
  "processing_time_seconds": 2.34
}
```

**Error Responses:**
- 400 Bad Request: Invalid input (unsupported audio format, invalid surah/ayah)
- 500 Internal Server Error: Analysis failed

---

#### POST /api/v1/recordings/analyze/quick

Quick analysis for repetition loop - focuses on a specific word.

**Request:**
- Content-Type: `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| user_id | string | Yes | User identifier |
| target_word_index | int | Yes | Index of word to focus on |
| audio_file | file | Yes | Audio file |

**Response (200 OK):**
```json
{
  "passed": true,
  "confidence": 0.85,
  "feedback": "Good pronunciation! Moving on."
}
```

---

### Correction Audio

#### GET /api/v1/correction/audio/{correction_id}

Get correction audio sample by ID.

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| correction_id | string | Correction identifier (e.g., "qa_01") |

**Response:**
- 200 OK: Returns audio file (audio/mpeg)
- 404 Not Found: Correction audio not found

---

#### GET /api/v1/correction/audio/{correction_id}/url

Get presigned URL for correction audio.

**Response (200 OK):**
```json
{
  "correction_id": "qa_01",
  "url": "https://bucket.s3.amazonaws.com/corrections/qa_01.mp3?...",
  "expires_in": 3600
}
```

---

#### GET /api/v1/correction/list

List all available correction audio samples.

**Response (200 OK):**
```json
{
  "corrections": [
    {"id": "qa_01", "path": "corrections/qaf_correct.mp3"},
    {"id": "madd_natural", "path": "corrections/madd_natural.mp3"}
  ]
}
```

---

### Human Review / Feedback

#### POST /api/v1/feedback/review

Submit human review for a flagged recording.

**Request:**
```json
{
  "recording_id": "550e8400-e29b-41d4-a716-446655440000",
  "reviewer_id": "reviewer-123",
  "error_reviews": [
    {
      "error_index": 0,
      "is_correct": true,
      "actual_error_type": null,
      "notes": null
    }
  ],
  "overall_assessment": "correct",
  "additional_errors": null,
  "notes": "Clear recording"
}
```

**Response (200 OK):**
```json
{
  "status": "accepted",
  "recording_id": "550e8400-e29b-41d4-a716-446655440000",
  "reviewer_id": "reviewer-123",
  "message": "Review submitted successfully."
}
```

---

#### GET /api/v1/feedback/queue

Get recordings pending human review.

**Query Parameters:**
| Name | Type | Default | Description |
|------|------|---------|-------------|
| reviewer_id | string | required | Reviewer identifier |
| limit | int | 10 | Maximum items to return |

**Response (200 OK):**
```json
{
  "queue": [
    {
      "recording_id": "mock-recording-001",
      "user_id": "user-123",
      "surah": 1,
      "ayah": 1,
      "low_confidence_errors": [
        {
          "type": "substituted_letter",
          "confidence": 0.55,
          "letter": "ق",
          "detected": "ك"
        }
      ],
      "created_at": "2024-01-15T10:30:00Z",
      "priority": 3
    }
  ],
  "total_pending": 45
}
```

---

#### POST /api/v1/feedback/flag

Flag a recording for human review.

**Request:**
```json
{
  "recording_id": "550e8400-e29b-41d4-a716-446655440000",
  "reason": "User disagrees with feedback",
  "flagged_by": "user-123"
}
```

**Response (200 OK):**
```json
{
  "status": "flagged",
  "recording_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Recording has been queued for expert review."
}
```

---

## Error Types

| Type | Description |
|------|-------------|
| substituted_letter | A letter was pronounced as a different letter |
| missing_word | A word was not detected in the recitation |
| madd_short | Elongation (madd) was too short |
| madd_long | Elongation (madd) was too long |
| ghunnah_missing | Required nasalization was not detected |
| ghunnah_short | Nasalization was too short |
| qalqalah_missing | Required qalqalah bounce was not detected |
| qalqalah_weak | Qalqalah was too weak |
| idgham_missing | Required idgham was not applied |
| ikhfa_missing | Required ikhfa was not applied |
| iqlab_missing | Required iqlab was not applied |

---

## Severity Levels

| Level | Description |
|-------|-------------|
| high | Critical error affecting meaning or major tajweed rule |
| medium | Moderate error in tajweed application |
| low | Minor issue, still acceptable |

---

## WebSocket API

### WS /ws/recite

Real-time recitation analysis with streaming feedback.

**Connection:**
```
ws://api.qari-app.com/ws/recite?user_id=xxx&surah=1&ayah=1
```

**Client → Server:**
```json
{
  "type": "audio_chunk",
  "data": "<base64-encoded-audio>",
  "sequence": 1
}
```

**Server → Client (interim):**
```json
{
  "type": "interim",
  "text": "بِسْمِ اللَّهِ",
  "confidence": 0.8
}
```

**Server → Client (final):**
```json
{
  "type": "final",
  "result": { /* same as POST /analyze response */ }
}
```
