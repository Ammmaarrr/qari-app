@echo off
REM Train all tajweed classifiers sequentially

echo ============================================
echo Training All Tajweed Classifiers
echo ============================================
echo.

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Check if training data exists
if not exist "data\ml_training\training_manifest.json" (
    echo ERROR: Training manifest not found!
    echo Please run: python scripts\download_ml_training_data.py
    pause
    exit /b 1
)

REM Train models for each tajweed rule
echo [1/6] Training Madd classifier...
python app\ml\train.py --error_type madd_2 --epochs 20

echo.
echo [2/6] Training Ghunnah classifier...
python app\ml\train.py --error_type ghunnah --epochs 20

echo.
echo [3/6] Training Qalqalah classifier...
python app\ml\train.py --error_type qalqalah --epochs 20

echo.
echo [4/6] Training Ikhfa classifier...
python app\ml\train.py --error_type ikhfa --epochs 20

echo.
echo [5/6] Training Idghaam classifier...
python app\ml\train.py --error_type idghaam_ghunnah --epochs 20

echo.
echo [6/6] Training Iqlab classifier...
python app\ml\train.py --error_type iqlab --epochs 20

echo.
echo ============================================
echo Training Complete!
echo ============================================
echo.
echo Models saved in: data\ml_training\
echo.
pause
