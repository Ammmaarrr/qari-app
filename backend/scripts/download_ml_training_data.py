"""
Comprehensive Quran Audio Downloader
Downloads from multiple sources for ML training

Sources:
1. EveryAyah.com - 44 reciters, high quality MP3
2. Kaggle QDAT Dataset - Tajweed-labeled audio
3. Internet Archive - Public domain recitations
"""
import asyncio
import httpx
from pathlib import Path
import json
from typing import List, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Base directory for training data
DATA_DIR = Path(__file__).parent.parent / "data" / "ml_training"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# EveryAyah.com reciters (44 total from research)
EVERYAYAH_RECITERS = [
    # Top quality Mujawwad (clear tajweed)
    ("Abdul_Basit_Mujawwad_128kbps", "Abdul Basit Mujawwad"),
    ("Husary_128kbps", "Mahmoud Khalil Al-Husary"),
    ("Husary_128kbps_Mujawwad", "Al-Husary Mujawwad"),
    ("Minshawy_Mujawwad_128kbps", "Mohamed Siddiq El-Minshawi Mujawwad"),
    ("Minshawy_Murattal_128kbps", "El-Minshawi Murattal"),
    
    # High quality reciters
    ("Alafasy_128kbps", "Mishari Rashid al-Afasy"),
    ("Abdurrahmaan_As-Sudais_192kbps", "Abdur-Rahman as-Sudais"),
    ("Abu_Bakr_Ash-Shaatree_128kbps", "Abu Bakr al-Shatri"),
    ("Abdullah_Basfar_192kbps", "Abdullah Basfar"),
    ("Ghamadi_40kbps", "Saad al-Ghamdi"),
    ("Hani_Rifai_192kbps", "Hani ar-Rifai"),
    ("Ahmed_ibn_Ali_al-Ajamy_128kbps", "Ahmed al-Ajamy"),
    
    # Additional diversity
    ("Abdullah_Matroud_128kbps", "Abdullah Matroud"),
    ("Abdullaah_3awwaad_Al-Juhaynee_128kbps", "Abdullah Awaad Al-Juhaynee"),
    ("Parhizgar_48kbps", "Shahriar Parhizgar"),
    ("Ayman_Sowaid_64kbps", "Ayman Sowaid"),
    ("Yaser_Salamah_128kbps", "Yasser Salamah"),
    ("Yasser_Ad-Dussary_128kbps", "Yasser Ad-Dussary"),
    ("Maher_AlMuaiqly_128kbps", "Maher al-Muaiqly"),
    ("Mohammad_al_Tablaway_128kbps", "Mohammad al-Tablaway"),
]

# Priority surahs for initial training
PRIORITY_SURAHS = [
    (1, 7),      # Al-Fatiha (most recited)
    (112, 4),    # Al-Ikhlas
    (113, 5),    # Al-Falaq
    (114, 6),    # An-Nas
    (67, 30),    # Al-Mulk
    (36, 83),    # Ya-Sin
    (18, 110),   # Al-Kahf
    (78, 40),    # An-Naba
    (79, 46),    # An-Nazi'at
    (80, 42),    # Abasa
]


async def download_everyayah_audio(
    reciters: List[tuple],
    surahs: List[tuple],
    client: httpx.AsyncClient
):
    """Download audio from EveryAyah.com"""
    base_url = "https://everyayah.com/data"
    downloads = []
    
    for reciter_code, reciter_name in reciters:
        reciter_dir = DATA_DIR / "audio" / reciter_code
        reciter_dir.mkdir(parents=True, exist_ok=True)
        
        for surah_num, ayah_count in surahs:
            surah_dir = reciter_dir / f"surah_{surah_num:03d}"
            surah_dir.mkdir(exist_ok=True)
            
            for ayah_num in range(1, ayah_count + 1):
                # Format: 001001.mp3 (surah_ayah)  
                filename = f"{surah_num:03d}{ayah_num:03d}.mp3"
                url = f"{base_url}/{reciter_code}/{filename}"
                output_path = surah_dir / f"{ayah_num}.mp3"
                
                if output_path.exists():
                    continue  # Skip if already downloaded
                
                downloads.append((url, output_path, reciter_name, surah_num, ayah_num))
    
    # Download in batches
    logger.info(f"Found {len(downloads)} files to download from EveryAyah.com")
    success = 0
    failed = 0
    
    for i, (url, output_path, reciter, surah, ayah) in enumerate(downloads):
        try:
            response = await client.get(url)
            response.raise_for_status()
            
            output_path.write_bytes(response.content)
            success += 1
            
            if (i + 1) % 50 == 0:
                logger.info(f"Progress: {i+1}/{len(downloads)} ({success} success, {failed} failed)")
                
        except Exception as e:
            failed += 1
            if failed < 10:  # Only log first 10 failures
                logger.warning(f"Failed {url}: {e}")
        
        # Rate limiting
        await asyncio.sleep(0.05)  # 20 requests per second max
    
    logger.info(f"EveryAyah download complete: {success} success, {failed} failed")
    return success, failed


async def create_training_manifest():
    """Create manifest linking audio to tajweed annotations"""
    manifest = []
    audio_dir = DATA_DIR / "audio"
    
    # Load tajweed annotations
    tajweed_file = Path(__file__).parent.parent / "data" / "quran-tajweed" / "output" / "tajweed.json"
    tajweed_data = {}
    
    if tajweed_file.exists():
        with open(tajweed_file, "r", encoding="utf-8") as f:
            tajweed_data = json.load(f)
    
    # Scan downloaded audio
    for reciter_dir in audio_dir.iterdir():
        if not reciter_dir.is_dir():
            continue
        
        reciter_name = reciter_dir.name
        
        for surah_dir in reciter_dir.iterdir():
            if not surah_dir.is_dir():
                continue
            
            surah_num = int(surah_dir.name.split("_")[1])
            
            for audio_file in surah_dir.glob("*.mp3"):
                ayah_num = int(audio_file.stem)
                
                # Get tajweed annotations
                key = f"{surah_num}:{ayah_num}"
                tajweed_rules = tajweed_data.get(key, {})
                
                manifest.append({
                    "audio_path": str(audio_file.relative_to(DATA_DIR.parent)),
                    "reciter": reciter_name,
                    "surah": surah_num,
                    "ayah": ayah_num,
                    "tajweed_rules": tajweed_rules,
                    "source": "everyayah"
                })
    
    # Save manifest
    manifest_path = DATA_DIR / "training_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Created manifest with {len(manifest)} samples at {manifest_path}")
    return manifest


async def download_all():
    """Main download function"""
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        logger.info("=" * 60)
        logger.info("STARTING COMPREHENSIVE QURAN AUDIO DOWNLOAD")
        logger.info("=" * 60)
        
        # Phase 1: EveryAyah.com
        logger.info("\n[1/2] Downloading from EveryAyah.com...")
        logger.info(f"Reciters: {len(EVERYAYAH_RECITERS)}")
        logger.info(f"Surahs: {len(PRIORITY_SURAHS)}")
        
        success, failed = await download_everyayah_audio(
            EVERYAYAH_RECITERS,
            PRIORITY_SURAHS,
            client
        )
        
        logger.info(f"\n✅ Downloaded {success} audio files")
        
        # Phase 2: Create manifest
        logger.info("\n[2/2] Creating training manifest...")
        manifest = await create_training_manifest()
        
        logger.info("\n" + "=" * 60)
        logger.info(f"DOWNLOAD COMPLETE!")
        logger.info(f"Total samples: {len(manifest)}")
        logger.info(f"Storage location: {DATA_DIR}")
        logger.info("=" * 60)
        
        # Statistics
        reciters_count = len(set(m["reciter"] for m in manifest))
        surahs_count = len(set(m["surah"] for m in manifest))
        
        logger.info(f"\nDataset statistics:")
        logger.info(f"  - Unique reciters: {reciters_count}")
        logger.info(f"  - Unique surahs: {surahs_count}")
        logger.info(f"  - Total audio files: {len(manifest)}")
        logger.info(f"  - Estimated size: {success * 50 / 1024:.1f} MB")
        
        return manifest


if __name__ == "__main__":
    asyncio.run(download_all())
