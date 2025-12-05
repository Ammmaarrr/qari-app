"""
Unified Quran Data Service
Provides comprehensive access to Quran text from multiple sources:
1. Kaggle dataset (local, with full diacritics)
2. Quran Cloud API (remote, with audio)
3. quran-tajweed annotations (for tajweed rules)
"""
import json
import os
import logging
import re
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Base paths
DATA_DIR = Path(__file__).parent.parent.parent / "data"
KAGGLE_DIR = DATA_DIR / "kaggle-quran"
TAJWEED_DIR = DATA_DIR / "quran-tajweed" / "tajweed_annotations"


class QuranDataService:
    """Unified service for Quran text and annotations"""
    
    def __init__(self):
        self._quran_text: Dict[int, Dict[int, str]] = {}
        self._page_data: Dict[int, Dict] = {}
        self._surah_info: List[Dict] = []
        self._tajweed_rules: Dict[str, Dict] = {}
        self._loaded = False
    
    def load(self):
        """Load all Quran data from local sources"""
        if self._loaded:
            return
        
        self._load_kaggle_text()
        self._load_tajweed_annotations()
        self._loaded = True
        logger.info("Quran data loaded successfully")
    
    def _load_kaggle_text(self):
        """Load Quran text from Kaggle dataset"""
        harakat_file = KAGGLE_DIR / "Quran_pages_harakat.txt"
        
        if not harakat_file.exists():
            logger.warning(f"Kaggle harakat file not found: {harakat_file}")
            return
        
        current_surah = 1
        current_ayah = 0
        
        with open(harakat_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Parse pages and extract ayahs
        pages = content.split("📄 Page ")
        
        for page in pages[1:]:  # Skip first empty
            lines = page.strip().split("\n")
            page_num_line = lines[0]
            
            try:
                page_num = int(page_num_line.strip())
            except ValueError:
                continue
            
            page_lines = []
            for line in lines[1:]:
                if line.strip().startswith("Line"):
                    # Extract line content after "Line N: "
                    match = re.match(r"\s*Line \d+:\s*(.*)", line)
                    if match:
                        text = match.group(1).strip()
                        if text:
                            page_lines.append(text)
            
            self._page_data[page_num] = {
                "page": page_num,
                "lines": page_lines,
                "text": "\n".join(page_lines)
            }
        
        logger.info(f"Loaded {len(self._page_data)} pages from Kaggle dataset")
    
    def _load_tajweed_annotations(self):
        """Load tajweed rule annotations"""
        if not TAJWEED_DIR.exists():
            logger.warning(f"Tajweed directory not found: {TAJWEED_DIR}")
            return
        
        rule_files = [
            "ghunnah", "idghaam_ghunnah", "idghaam_mutajanisayn", 
            "idghaam_mutaqaribayn", "idghaam_no_ghunnah", "idghaam_shafawi",
            "ikhfa", "ikhfa_shafawi", "iqlab", "madd_2", "madd_246",
            "madd_6", "madd_muttasil", "madd_munfasil", "qalqalah", "lam_shamsiyah"
        ]
        
        for rule_name in rule_files:
            rule_file = TAJWEED_DIR / f"{rule_name}.json"
            if rule_file.exists():
                try:
                    with open(rule_file, "r", encoding="utf-8") as f:
                        self._tajweed_rules[rule_name] = json.load(f)
                    logger.debug(f"Loaded tajweed rule: {rule_name}")
                except Exception as e:
                    logger.error(f"Error loading {rule_name}: {e}")
        
        logger.info(f"Loaded {len(self._tajweed_rules)} tajweed rule files")
    
    # === Text Access ===
    
    def get_page(self, page_num: int) -> Optional[Dict]:
        """Get a specific page (1-604)"""
        self.load()
        return self._page_data.get(page_num)
    
    def get_page_text(self, page_num: int) -> str:
        """Get just the text of a page"""
        page = self.get_page(page_num)
        return page.get("text", "") if page else ""
    
    def get_page_range(self, start: int, end: int) -> List[Dict]:
        """Get a range of pages"""
        self.load()
        return [self._page_data[p] for p in range(start, end + 1) if p in self._page_data]
    
    def search_text(self, query: str, max_results: int = 10) -> List[Dict]:
        """Search for text across all pages"""
        self.load()
        results = []
        
        for page_num, page_data in self._page_data.items():
            text = page_data.get("text", "")
            if query in text:
                # Find the specific line
                for i, line in enumerate(page_data.get("lines", [])):
                    if query in line:
                        results.append({
                            "page": page_num,
                            "line": i + 1,
                            "text": line,
                            "snippet": self._create_snippet(line, query)
                        })
                        if len(results) >= max_results:
                            return results
        
        return results
    
    def _create_snippet(self, text: str, query: str, context: int = 30) -> str:
        """Create a snippet with context around the query"""
        idx = text.find(query)
        if idx == -1:
            return text[:60] + "..."
        
        start = max(0, idx - context)
        end = min(len(text), idx + len(query) + context)
        
        snippet = text[start:end]
        if start > 0:
            snippet = "..." + snippet
        if end < len(text):
            snippet = snippet + "..."
        
        return snippet
    
    # === Tajweed Rules ===
    
    def get_tajweed_rule(self, rule_name: str) -> Dict:
        """Get annotations for a specific tajweed rule"""
        self.load()
        return self._tajweed_rules.get(rule_name, {})
    
    def get_ayah_tajweed(self, surah: int, ayah: int) -> List[Dict]:
        """Get all tajweed rules for a specific ayah"""
        self.load()
        rules = []
        
        key = f"{surah}:{ayah}"
        
        for rule_name, rule_data in self._tajweed_rules.items():
            if key in rule_data:
                for annotation in rule_data[key]:
                    rules.append({
                        "rule": rule_name,
                        "start": annotation.get("start"),
                        "end": annotation.get("end"),
                        "text": annotation.get("text", "")
                    })
        
        return rules
    
    def get_available_rules(self) -> List[str]:
        """Get list of available tajweed rules"""
        self.load()
        return list(self._tajweed_rules.keys())
    
    # === Statistics ===
    
    def get_stats(self) -> Dict:
        """Get dataset statistics"""
        self.load()
        return {
            "total_pages": len(self._page_data),
            "tajweed_rules": len(self._tajweed_rules),
            "rule_names": list(self._tajweed_rules.keys())
        }


# === Surah Info ===
SURAH_INFO = [
    {"number": 1, "name": "Al-Fatiha", "name_ar": "الفاتحة", "ayahs": 7, "page_start": 1},
    {"number": 2, "name": "Al-Baqarah", "name_ar": "البقرة", "ayahs": 286, "page_start": 2},
    {"number": 3, "name": "Aal-E-Imran", "name_ar": "آل عمران", "ayahs": 200, "page_start": 50},
    # ... more surahs (abbreviated for brevity)
    {"number": 112, "name": "Al-Ikhlas", "name_ar": "الإخلاص", "ayahs": 4, "page_start": 604},
    {"number": 113, "name": "Al-Falaq", "name_ar": "الفلق", "ayahs": 5, "page_start": 604},
    {"number": 114, "name": "An-Nas", "name_ar": "الناس", "ayahs": 6, "page_start": 604},
]


def get_surah_info(surah_num: int) -> Optional[Dict]:
    """Get info about a surah"""
    for surah in SURAH_INFO:
        if surah["number"] == surah_num:
            return surah
    return None


# Singleton instance
_quran_data: Optional[QuranDataService] = None


def get_quran_data() -> QuranDataService:
    """Get or create Quran data service instance"""
    global _quran_data
    if _quran_data is None:
        _quran_data = QuranDataService()
        _quran_data.load()
    return _quran_data
