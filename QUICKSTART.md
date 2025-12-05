# Qari App - Quick Start Guide

## 🚀 Start Backend API

```powershell
cd backend
.\run_backend.bat
```

The backend will start at **http://localhost:8000**

- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

---

## 📱 Start Mobile App

```bash
cd mobile
npm start
```

Then:
- Press `a` for Android emulator
- Press `i` for iOS simulator  
- Scan QR code with Expo Go app

---

## ✅ What's Working

| Feature | Status |
|---------|--------|
| Complete Quran database (6,236 ayahs) | ✅ |
| Audio normalization | ✅ |
| Whisper ASR transcription | ✅ |
| Verse matching (all 114 surahs) | ✅ |
| Tajweed detectors (madd/ghunnah/qalqalah) | ✅ |
| Mobile recording UI | ✅ |
| API endpoints | ✅ |

---

## 🎬 Try It Now

### Test API Manually

1. Open http://localhost:8000/docs
2. Expand `POST /api/v1/recordings/analyze`
3. Click "Try it out"
4. Upload an MP3 file of Quran recitation
5. Click "Execute"
6. View tajweed analysis results

### Test Mobile App

1. Start mobile app: `npm start`
2. Record Surah Al-Fatiha (1:1)
3. See real-time analysis
4. Review detected errors

---

## 📊 System Requirements

- Python 3.10+ with pip
- Node.js 16+ with npm
- FFmpeg (included in `backend/bin/`)
- 2GB free disk space

---

## 🐛 Troubleshooting

**Backend won't start?**
```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

**Quran database missing?**
```powershell
cd backend
.venv\Scripts\python scripts\download_quran_database.py
```

**Mobile app errors?**
```bash
cd mobile
rm -rf node_modules
npm install
```

---

## 📝 API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/ready` | GET | Readiness check |
| `/api/v1/recordings/analyze` | POST | Analyze recitation |
| `/docs` | GET | Swagger UI |

---

## 🎯 Next Steps

1. ✅  Backend running
2. ✅ Mobile app running
3. 🔄 Train ML models (optional)
4. 🔄 Deploy to production

---

## 💡 Tips

- **Rule-based detection** works without ML models (60-70% accuracy)
- **ML models** require training data (80%+ accuracy after training)
- Start with rule-based, collect user data, train models later
- All 114 surahs are supported out of the box

---

## 📞 Support

- Check `docs/` for detailed documentation
- Review `backend/README.md` for API details
- See `mobile/README.md` for mobile setup
