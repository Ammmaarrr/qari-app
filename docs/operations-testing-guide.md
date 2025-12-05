# Qari App - Operations Testing Guide

## Quick Start Operations Testing

Follow these steps to test your locally running Qari App system.

---

## 1. Verify Backend is Running

Your backend should already be running on port 8000. Let's verify:

```bash
# Check if backend is responding
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","service":"qari-app-api"}
```

If not running, start it:

```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 2. Access API Documentation

Open your browser and navigate to:

**Swagger UI**: http://localhost:8000/docs  
**ReDoc**: http://localhost:8000/redoc

This shows all available endpoints interactively.

---

## 3. Test Core Endpoints

### Health Check
```bash
curl http://localhost:8000/health
```

### Readiness Check
```bash
curl http://localhost:8000/ready
```

### List Available Corrections
```bash
curl http://localhost:8000/api/v1/correction/list
```

---

## 4. Test Audio Analysis (Manual)

### Create a test audio file

Since you're on Windows, you can:

**Option A**: Record a short recitation using Voice Recorder  
**Option B**: Use a test audio file

### Test the analyze endpoint

```powershell
# Using PowerShell
$audioPath = "C:\path\to\your\test.wav"

curl.exe -X POST http://localhost:8000/api/v1/recordings/analyze `
  -F "user_id=test-user-$(Get-Date -Format 'yyyyMMddHHmmss')" `
  -F "surah=1" `
  -F "ayah=1" `
  -F "mode=short" `
  -F "audio_file=@$audioPath"
```

**Expected Response**:
```json
{
  "request_id": "...",
  "matched_ayah": {
    "surah": 1,
    "ayah": 1,
    "confidence": 0.85,
    "text": "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"
  },
  "errors": [...],
  "overall_score": 0.78,
  "recommendation": "...",
  "processing_time_seconds": 2.34
}
```

---

## 5. Test Frontend Design System

Your frontend-design should be running on port 3001:

Open browser: http://localhost:3001

This shows the UI prototypes and design system.

---

## 6. Run Backend Tests

```bash
cd backend

# Run all tests
pytest tests/ -v

# Run specific test module
pytest tests/test_api_integration.py -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
# Then open: htmlcov/index.html
```

---

## 7. Check Backend Logs

The backend should be logging to console. Look for:

- ✅ Startup messages
- ✅ Model loading (Whisper)
- ✅ Request processing
- ⚠️ Any errors or warnings

---

## 8. Test Label Studio (Optional)

Start Label Studio for data annotation:

```bash
cd backend/docker
docker-compose -f label-studio-compose.yml up -d

# Access: http://localhost:8080
# Default credentials: Create admin account on first visit
```

---

## 9. Performance Benchmarking

### Test response times

```bash
# Create a simple benchmark
for i in {1..5}; do
  echo "Request $i:"
  curl -w "\nTime: %{time_total}s\n" \
    -X GET http://localhost:8000/health
done
```

### Expected metrics
- Health check: < 100ms
- Analyze endpoint: 2-10s (depends on audio length and Whisper model)

---

## 10. Mobile App Testing

If you want to test the mobile app:

```bash
cd mobile

# iOS (requires macOS + Xcode)
npm run ios

# Android (requires Android Studio)
npm run android
```

**Update API endpoint in mobile app**:
Edit `mobile/src/services/api.ts`:
```typescript
const API_BASE_URL = 'http://localhost:8000';  // Development
// const API_BASE_URL = 'http://192.168.1.X:8000';  // Use your local IP for device testing
```

---

## Common Issues & Solutions

### Issue: curl command not found
**Solution**: Use `curl.exe` on Windows or install via `winget install curl`

### Issue: Backend not responding
**Solution**: 
```bash
# Check if process is running
netstat -ano | findstr :8000

# Kill process if needed
taskkill /PID <PID> /F

# Restart backend
cd backend
python -m uvicorn app.main:app --reload
```

### Issue: Module not found errors
**Solution**:
```bash
cd backend
pip install -r requirements.txt
```

### Issue: GPU not detected (if testing ML)
**Solution**: This is expected on development machine. GPU is only needed for production. The code will fall back to CPU.

---

## Next Steps After Local Testing

Once local testing is successful:

1. **Collect Sample Data**
   - Record 10-20 sample recitations
   - Test with different voices and quality levels

2. **Prepare for Cloud Deployment**
   - Review AWS credentials
   - Update `.env` with production values
   - Run through deployment guide

3. **Setup Monitoring**
   - Configure error tracking (Sentry)
   - Setup log aggregation
   - Create dashboards

---

## Quick Test Checklist

- [ ] Backend health endpoint responds
- [ ] API docs accessible at /docs
- [ ] Can upload audio file
- [ ] Receive analysis response
- [ ] Frontend-design loads in browser
- [ ] Backend tests pass
- [ ] No critical errors in logs

**Once all checked, you're ready for deployment!**
