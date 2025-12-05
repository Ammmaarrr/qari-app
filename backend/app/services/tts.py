"""
Text-to-Speech Service
Generate correction audio samples
"""
import logging
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class TTSService:
    """
    Text-to-Speech service for generating correction audio.
    
    Supports multiple backends:
    - local: Use Coqui TTS (open source)
    - google: Google Cloud TTS
    - amazon: Amazon Polly
    """
    
    def __init__(self, provider: str = "local"):
        self.provider = provider
        self._model = None
        
    def generate_audio(
        self,
        text: str,
        output_path: str,
        voice: str = "ar-XA-Wavenet-A",
        speed: float = 0.85
    ) -> str:
        """
        Generate audio file from Arabic text.
        
        Args:
            text: Arabic text to speak
            output_path: Where to save the audio file
            voice: Voice identifier
            speed: Speaking rate (0.5-2.0)
            
        Returns:
            Path to generated audio file
        """
        if self.provider == "local":
            return self._generate_local(text, output_path, speed)
        elif self.provider == "google":
            return self._generate_google(text, output_path, voice, speed)
        elif self.provider == "amazon":
            return self._generate_amazon(text, output_path, voice, speed)
        else:
            raise ValueError(f"Unknown TTS provider: {self.provider}")
    
    def _generate_local(
        self,
        text: str,
        output_path: str,
        speed: float
    ) -> str:
        """Generate using Coqui TTS"""
        try:
            from TTS.api import TTS
            
            if self._model is None:
                # Load Arabic TTS model
                self._model = TTS(model_name="tts_models/ar/cv/vits")
            
            self._model.tts_to_file(
                text=text,
                file_path=output_path,
                speed=speed
            )
            
            return output_path
            
        except ImportError:
            logger.warning("Coqui TTS not installed. Returning placeholder.")
            return self._create_placeholder(output_path)
    
    def _generate_google(
        self,
        text: str,
        output_path: str,
        voice: str,
        speed: float
    ) -> str:
        """Generate using Google Cloud TTS"""
        try:
            from google.cloud import texttospeech
            
            client = texttospeech.TextToSpeechClient()
            
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            voice_params = texttospeech.VoiceSelectionParams(
                language_code="ar-XA",
                name=voice
            )
            
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=speed
            )
            
            response = client.synthesize_speech(
                input=synthesis_input,
                voice=voice_params,
                audio_config=audio_config
            )
            
            with open(output_path, "wb") as f:
                f.write(response.audio_content)
            
            return output_path
            
        except ImportError:
            logger.warning("Google Cloud TTS not installed.")
            return self._create_placeholder(output_path)
    
    def _generate_amazon(
        self,
        text: str,
        output_path: str,
        voice: str,
        speed: float
    ) -> str:
        """Generate using Amazon Polly"""
        try:
            import boto3
            
            client = boto3.client('polly')
            
            response = client.synthesize_speech(
                Text=text,
                OutputFormat='mp3',
                VoiceId='Zeina',  # Arabic voice
                LanguageCode='arb',
                Engine='neural'
            )
            
            with open(output_path, "wb") as f:
                f.write(response['AudioStream'].read())
            
            return output_path
            
        except Exception as e:
            logger.warning(f"Amazon Polly failed: {e}")
            return self._create_placeholder(output_path)
    
    def _create_placeholder(self, output_path: str) -> str:
        """Create placeholder file when TTS unavailable"""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).touch()
        logger.warning(f"Created placeholder audio: {output_path}")
        return output_path


# Pre-generated correction audio database
# In production, these would be recorded by qualified Qaris
CORRECTION_AUDIO_DB = {
    "qa_01": {
        "text": "ق",
        "description": "Letter Qaf pronounced correctly",
        "file": "corrections/qaf_correct.mp3"
    },
    "madd_natural": {
        "text": "بَا",
        "description": "Natural madd (2 counts)",
        "file": "corrections/madd_natural.mp3"
    },
    "ghunnah_noon": {
        "text": "نّ",
        "description": "Noon with ghunnah",
        "file": "corrections/ghunnah_noon.mp3"
    },
    "qalqalah_qaf": {
        "text": "قْ",
        "description": "Qaf with qalqalah",
        "file": "corrections/qalqalah_qaf.mp3"
    }
}


def get_correction_audio_path(correction_id: str) -> Optional[str]:
    """Get path to pre-recorded correction audio"""
    if correction_id in CORRECTION_AUDIO_DB:
        return CORRECTION_AUDIO_DB[correction_id]["file"]
    return None


# Singleton instance
_tts_service: Optional[TTSService] = None


def get_tts_service() -> TTSService:
    """Get TTS service singleton"""
    global _tts_service
    if _tts_service is None:
        from app.config import settings
        _tts_service = TTSService(provider=settings.TTS_PROVIDER)
    return _tts_service
