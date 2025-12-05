"""
Quran Cloud API Service
Provides access to Quran text, translations, and audio from alquran.cloud
"""
import logging
import httpx
from typing import Dict, Any, List, Optional
from functools import lru_cache

logger = logging.getLogger(__name__)

# Base URL for Quran Cloud API
QURAN_CLOUD_API = "https://api.alquran.cloud/v1"

# Audio CDN base for recitation audio
AUDIO_CDN_BASE = "https://cdn.alquran.cloud/media/audio/ayah"


class QuranCloudService:
    """Service for interacting with Quran Cloud API"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self._editions_cache = None
    
    async def close(self):
        await self.client.aclose()
    
    # === Edition Endpoints ===
    
    async def get_editions(
        self, 
        format: Optional[str] = None,  # 'text' or 'audio'
        language: Optional[str] = None,  # e.g., 'ar', 'en'
        edition_type: Optional[str] = None  # e.g., 'translation', 'versebyverse'
    ) -> List[Dict]:
        """Get available Quran editions"""
        params = {}
        if format:
            params['format'] = format
        if language:
            params['language'] = language
        if edition_type:
            params['type'] = edition_type
        
        response = await self.client.get(f"{QURAN_CLOUD_API}/edition", params=params)
        response.raise_for_status()
        data = response.json()
        return data.get('data', [])
    
    async def get_audio_editions(self, language: str = 'ar') -> List[Dict]:
        """Get available audio recitation editions"""
        return await self.get_editions(format='audio', language=language)
    
    # === Surah Endpoints ===
    
    async def get_surah(
        self, 
        surah_number: int, 
        edition: str = 'quran-uthmani'
    ) -> Dict[str, Any]:
        """Get a complete surah with text"""
        response = await self.client.get(f"{QURAN_CLOUD_API}/surah/{surah_number}/{edition}")
        response.raise_for_status()
        data = response.json()
        return data.get('data', {})
    
    async def get_surah_with_audio(
        self, 
        surah_number: int, 
        reciter: str = 'ar.alafasy'
    ) -> Dict[str, Any]:
        """Get a surah with audio URLs for each ayah"""
        response = await self.client.get(f"{QURAN_CLOUD_API}/surah/{surah_number}/{reciter}")
        response.raise_for_status()
        data = response.json()
        return data.get('data', {})
    
    async def get_all_surahs(self) -> List[Dict]:
        """Get list of all surahs with metadata"""
        response = await self.client.get(f"{QURAN_CLOUD_API}/surah")
        response.raise_for_status()
        data = response.json()
        return data.get('data', [])
    
    # === Ayah Endpoints ===
    
    async def get_ayah(
        self, 
        surah: int, 
        ayah: int, 
        edition: str = 'quran-uthmani'
    ) -> Dict[str, Any]:
        """Get a specific ayah"""
        reference = f"{surah}:{ayah}"
        response = await self.client.get(f"{QURAN_CLOUD_API}/ayah/{reference}/{edition}")
        response.raise_for_status()
        data = response.json()
        return data.get('data', {})
    
    async def get_ayah_with_audio(
        self, 
        surah: int, 
        ayah: int, 
        reciter: str = 'ar.alafasy'
    ) -> Dict[str, Any]:
        """Get a specific ayah with audio URL"""
        return await self.get_ayah(surah, ayah, reciter)
    
    async def get_ayah_range(
        self, 
        surah: int, 
        start_ayah: int, 
        end_ayah: int,
        edition: str = 'quran-uthmani'
    ) -> List[Dict]:
        """Get a range of ayahs"""
        ayahs = []
        for ayah_num in range(start_ayah, end_ayah + 1):
            ayah_data = await self.get_ayah(surah, ayah_num, edition)
            ayahs.append(ayah_data)
        return ayahs
    
    # === Juz Endpoints ===
    
    async def get_juz(self, juz_number: int, edition: str = 'quran-uthmani') -> Dict:
        """Get a complete juz (1-30)"""
        response = await self.client.get(f"{QURAN_CLOUD_API}/juz/{juz_number}/{edition}")
        response.raise_for_status()
        data = response.json()
        return data.get('data', {})
    
    # === Search ===
    
    async def search(self, keyword: str, surah: Optional[int] = None, edition: str = 'en.asad') -> Dict:
        """Search the Quran for a keyword"""
        url = f"{QURAN_CLOUD_API}/search/{keyword}/{edition}"
        if surah:
            url += f"/{surah}"
        response = await self.client.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get('data', {})
    
    # === Audio Helpers ===
    
    def get_audio_url(self, surah: int, ayah: int, reciter: str = 'ar.alafasy') -> str:
        """Generate audio URL for an ayah"""
        # Format: https://cdn.alquran.cloud/media/audio/ayah/ar.alafasy/1
        ayah_number = self._get_absolute_ayah_number(surah, ayah)
        return f"{AUDIO_CDN_BASE}/{reciter}/{ayah_number}"
    
    def _get_absolute_ayah_number(self, surah: int, ayah: int) -> int:
        """Convert surah:ayah to absolute ayah number (1-6236)"""
        # Approximate - in production, use proper lookup table
        ayah_counts = [
            0, 7, 286, 200, 176, 120, 165, 206, 75, 129, 109,  # 1-10
            123, 111, 43, 52, 99, 128, 111, 110, 98, 135,  # 11-20
            112, 78, 118, 64, 77, 227, 93, 88, 69, 60,  # 21-30
            34, 30, 73, 54, 45, 83, 182, 88, 75, 85,  # 31-40
            54, 53, 89, 59, 37, 35, 38, 29, 18, 45,  # 41-50
            60, 49, 62, 55, 78, 96, 29, 22, 24, 13,  # 51-60
            14, 11, 11, 18, 12, 12, 30, 52, 52, 44,  # 61-70
            28, 28, 20, 56, 40, 31, 50, 40, 46, 42,  # 71-80
            29, 19, 36, 25, 22, 17, 19, 26, 30, 20,  # 81-90
            15, 21, 11, 8, 8, 19, 5, 8, 8, 11,  # 91-100
            11, 8, 3, 9, 5, 4, 7, 3, 6, 3,  # 101-110
            5, 4, 5, 6  # 111-114
        ]
        
        absolute = sum(ayah_counts[:surah]) + ayah
        return absolute


# Singleton instance
_quran_service: Optional[QuranCloudService] = None


async def get_quran_service() -> QuranCloudService:
    """Get or create Quran Cloud service instance"""
    global _quran_service
    if _quran_service is None:
        _quran_service = QuranCloudService()
    return _quran_service


# === Utility Functions ===

async def get_ayah_text(surah: int, ayah: int) -> str:
    """Quick helper to get ayah text"""
    service = await get_quran_service()
    data = await service.get_ayah(surah, ayah)
    return data.get('text', '')


async def get_surah_metadata(surah: int) -> Dict:
    """Get surah name and metadata"""
    service = await get_quran_service()
    surahs = await service.get_all_surahs()
    for s in surahs:
        if s.get('number') == surah:
            return s
    return {}


async def get_correction_audio_url(surah: int, ayah: int, reciter: str = 'ar.alafasy') -> str:
    """Get URL for correct recitation audio"""
    service = await get_quran_service()
    return service.get_audio_url(surah, ayah, reciter)


# Available reciters (popular ones)
POPULAR_RECITERS = {
    'ar.alafasy': 'Mishary Alafasy',
    'ar.abdulbasitmurattal': 'Abdul Basit (Murattal)',
    'ar.abdulbasitmujawwad': 'Abdul Basit (Mujawwad)',
    'ar.husary': 'Mahmoud Khalil Al-Husary',
    'ar.husarymujawwad': 'Al-Husary (Mujawwad)',
    'ar.minshawi': 'Mohamed Siddiq El-Minshawi',
    'ar.minshawimujawwad': 'El-Minshawi (Mujawwad)',
    'ar.parhizgar': 'Shahriar Parhizgar',
    'ar.shaatree': 'Abu Bakr Al-Shatri',
    'ar.ahmedajamy': 'Ahmed Al-Ajmi',
}
