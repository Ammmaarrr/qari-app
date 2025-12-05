"""
Load complete Quran database from Quran Cloud API
This script downloads all 114 surahs and saves them locally
"""
import json
import httpx
import asyncio
from pathlib import Path

API_BASE = "https://api.alquran.cloud/v1"
DATA_DIR = Path(__file__).parent.parent / "data"
OUTPUT_FILE = DATA_DIR / "quran_uthmani.json"


async def download_quran():
    """Download all 114 surahs from Quran Cloud API"""
    quran_data = {}
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for surah_num in range(1, 115):
            print(f"Downloading Surah {surah_num}/114...", end=" ")
            
            try:
                response = await client.get(f"{API_BASE}/surah/{surah_num}/quran-uthmani")
                response.raise_for_status()
                data = response.json()
                
                surah_data = data["data"]
                ayahs = {}
                
                for ayah in surah_data["ayahs"]:
                    ayah_number = ayah["numberInSurah"]
                    ayahs[ayah_number] = ayah["text"]
                
                quran_data[surah_num] = {
                    "name": surah_data["name"],
                    "englishName": surah_data["englishName"],
                    "revelationType": surah_data["revelationType"],
                    "numberOfAyahs": surah_data["numberOfAyahs"],
                    "ayahs": ayahs
                }
                
                print(f"✓ ({surah_data['numberOfAyahs']} ayahs)")
                
            except Exception as e:
                print(f"✗ Error: {e}")
                continue
            
            # Small delay to be respectful to API
            await asyncio.sleep(0.1)
    
    # Save to file
    DATA_DIR.mkdir(exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(quran_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Downloaded {len(quran_data)} surahs")
    print(f"💾 Saved to: {OUTPUT_FILE}")
    
    return quran_data


if __name__ == "__main__":
    asyncio.run(download_quran())
