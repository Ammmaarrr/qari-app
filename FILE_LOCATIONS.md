# Qari App - File Locations Guide

## Current Project Location

Your complete qari-app project is at:
```
C:\Users\ahmad uzair shah\.gemini\antigravity\playground\scalar-nebula\qari-app
```

## What's Inside

### Backend (API)
```
backend/
├── app/                      # All Python code
│   ├── ml/train.py          # ML training script
│   └── services/            # Tajweed detectors
├── data/
│   ├── quran_uthmani.json           # Complete Quran (6,236 ayahs)
│   ├── kaggle-quran/                # 604 pages with diacritics
│   ├── quran-tajweed/               # Tajweed annotations
│   └── ml_training/
│       └── audio/                   # 4,388 MP3 files (downloading)
├── run_backend.bat          # Start API server
└── train_all_models.bat     # Train ML models
```

### Mobile App  
```
mobile/                      # React Native app
├── src/                     # TypeScript source code
└── package.json             # Dependencies
```

---

## How to Access Files

### Option 1: Open in File Explorer
1. Press `Win + R`
2. Paste: `C:\Users\ahmad uzair shah\.gemini\antigravity\playground\scalar-nebula\qari-app`
3. Press Enter

### Option 2: Copy to Desktop (Recommended)

Run this command to copy everything to Desktop:

```powershell
# Copy project to Desktop
robocopy "C:\Users\ahmad uzair shah\.gemini\antigravity\playground\scalar-nebula\qari-app" "$env:USERPROFILE\Desktop\qari-app" /E /Z /R:3 /W:5 /MT:8 /XD .git node_modules .venv __pycache__

# Then open Desktop folder
explorer "$env:USERPROFILE\Desktop\qari-app"
```

---

## Downloaded Audio Files

**Location**: `backend\data\ml_training\audio\`

**Count**: 4,388 files (and growing!)

**Organized by**:
- Reciter (20 folders)
  - Surah (10 folders per reciter)
    - Ayah (MP3 files)

Example:
```
audio/
├── Abdul_Basit_Mujawwad_128kbps/
│   ├── surah_001/
│   │   ├── 1.mp3
│   │   ├── 2.mp3
│   │   └── ...
│   ├── surah_112/
│   └── ...
├── Husary_128kbps/
└── Alafasy_128kbps/
```

---

## File Sizes

| Component | Size |
|-----------|------|
| Downloaded audio (4,388 files) | ~220 MB |
| Quran database | ~5 MB |
| Kaggle dataset | ~2 MB |
| Code + dependencies | ~800 MB (with venv) |
| **Total** | ~1 GB |

---

## Quick Actions

### View Downloaded Audio
```powershell
explorer "C:\Users\ahmad uzair shah\.gemini\antigravity\playground\scalar-nebula\qari-app\backend\data\ml_training\audio"
```

### Check Download Progress
The download is still running - you currently have:
- ✅ 4,388 files downloaded
- 🔄 ~3,000 more downloading
- ⏱ ETA: ~1-2 hours for completion

---

## Why .gemini Folder?

This is a workspace folder used by the development environment. It's perfectly fine to use the project from here, OR you can copy it to Desktop for easier access.

**Both locations will work!**

---

## Need to Move It?

If you want it on Desktop, here's what to do:

1. **Stop the download** (optional - it will continue from where it left off)
2. **Copy the entire folder** to Desktop
3. **Restart the download** from the new location

Or just **use it where it is** - everything works the same!
