"""
Quran Audio Dataset Downloader
Downloads recitation audio from EveryAyah.com for training data
"""
import os
import urllib.request
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import time

# EveryAyah.com base URL
BASE_URL = "https://everyayah.com/data"

# High-quality reciters for training (Mujawwad = with tajweed)
RECITERS = [
    "Husary_Muallim_128kbps",  # Teaching recitation - clear tajweed
    "Husary_128kbps_Mujawwad",  # Mujawwad style
    "Minshawy_Mujawwad_192kbps",  # Mujawwad style
    "Abdul_Basit_Mujawwad_128kbps",  # Mujawwad style
]

# Surahs to download (start with shorter ones)
SURAHS = [
    (1, 7),    # Al-Fatiha (7 ayahs)
    (112, 4),  # Al-Ikhlas (4 ayahs)
    (113, 5),  # Al-Falaq (5 ayahs)
    (114, 6),  # An-Nas (6 ayahs)
    (2, 286),  # Al-Baqarah (286 ayahs) - largest
]

def download_ayah(reciter: str, surah: int, ayah: int, output_dir: Path) -> bool:
    """Download a single ayah audio file"""
    # Format: 001001.mp3 = Surah 1, Ayah 1
    filename = f"{surah:03d}{ayah:03d}.mp3"
    url = f"{BASE_URL}/{reciter}/{filename}"
    output_path = output_dir / reciter / f"surah_{surah:03d}" / filename
    
    # Skip if already exists
    if output_path.exists():
        return True
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        urllib.request.urlretrieve(url, output_path)
        print(f"✓ Downloaded: {reciter}/{filename}")
        return True
    except Exception as e:
        print(f"✗ Failed: {reciter}/{filename} - {e}")
        return False

def download_surah(reciter: str, surah: int, num_ayahs: int, output_dir: Path):
    """Download all ayahs for a surah"""
    print(f"\nDownloading Surah {surah} from {reciter}...")
    success = 0
    for ayah in range(1, num_ayahs + 1):
        if download_ayah(reciter, surah, ayah, output_dir):
            success += 1
        time.sleep(0.1)  # Be respectful to the server
    print(f"Completed: {success}/{num_ayahs} ayahs")

def create_dataset_manifest(output_dir: Path, tajweed_json: Path):
    """Create a manifest linking audio to tajweed annotations"""
    # Load tajweed annotations
    with open(tajweed_json, 'r', encoding='utf-8') as f:
        tajweed_data = json.load(f)
    
    manifest = []
    for item in tajweed_data:
        surah = item['surah']
        ayah = item['ayah']
        annotations = item['annotations']
        
        # Find audio files for this ayah
        for reciter in RECITERS:
            filename = f"{surah:03d}{ayah:03d}.mp3"
            audio_path = output_dir / reciter / f"surah_{surah:03d}" / filename
            
            if audio_path.exists():
                manifest.append({
                    "audio_path": str(audio_path),
                    "reciter": reciter,
                    "surah": surah,
                    "ayah": ayah,
                    "tajweed_rules": [a['rule'] for a in annotations],
                    "annotations": annotations
                })
    
    # Save manifest
    manifest_path = output_dir / "training_manifest.json"
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    
    print(f"\nCreated manifest with {len(manifest)} samples: {manifest_path}")
    return manifest

def main():
    output_dir = Path("data/training/audio")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 50)
    print("Quran Audio Dataset Downloader")
    print("=" * 50)
    
    # Download audio for each surah
    total_files = 0
    for reciter in RECITERS:
        for surah, num_ayahs in SURAHS[:4]:  # Start with short surahs
            download_surah(reciter, surah, num_ayahs, output_dir)
            total_files += num_ayahs
    
    print(f"\n{'=' * 50}")
    print(f"Download complete! Total: ~{total_files * len(RECITERS)} files")
    
    # Create manifest if tajweed data available
    tajweed_json = Path("data/quran-tajweed/output/tajweed.hafs.uthmani-pause-sajdah.json")
    if tajweed_json.exists():
        create_dataset_manifest(output_dir, tajweed_json)

if __name__ == "__main__":
    main()
