# services/tts_service.py
import logging
import aiohttp
import aiofiles
from pathlib import Path
from typing import Optional

from app.config import settings
from utils.exceptions import TTSError

logger = logging.getLogger(__name__)

class TTSService:
    """Serviço de Text-to-Speech usando Piper TTS"""
    
    def __init__(self):
        self.base_url = settings.TTS_SERVICE_URL
        self.default_voice = settings.DEFAULT_VOICE
        self.timeout = aiohttp.ClientTimeout(total=30)
        
    async def synthesize_speech(self, text: str, output_filename: Optional[str] = None) -> str:
        """Sintetiza texto em áudio usando Piper TTS"""
        
        if not text or len(text.strip()) == 0:
            raise TTSError("Texto vazio fornecido para síntese")
        
        if len(text) > 5000:  # Limite de caracteres
            text = text[:4997] + "..."
            logger.warning("⚠️ Texto truncado para síntese TTS")
        
        # Define output path
        if not output_filename:
            import time
            output_filename = f"tts_output_{int(time.time())}.wav"
        
        output_path = Path("temp") / output_filename
        output_path.parent.mkdir(exist_ok=True)
        
        try:
            logger.info(f"🔊 Iniciando síntese TTS: {len(text)} caracteres")
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                # Prepare request parameters
                params = {
                    'text': text,
                    'voice': self.default_voice,
                    'speed': settings.TTS_SPEED
                }
                
                async with session.get(self.base_url, params=params) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        raise TTSError(f"TTS API error {response.status}: {error_text}")
                    
                    # Save audio content to file
                    async with aiofiles.open(output_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            await f.write(chunk)
                    
                    logger.info(f"✅ Síntese TTS concluída: {output_path}")
                    return str(output_path)
                    
        except aiohttp.ClientError as e:
            logger.error(f"❌ Erro de conexão TTS: {str(e)}")
            raise TTSError(f"Erro de conexão com serviço TTS: {str(e)}")
        
        except Exception as e:
            logger.error(f"❌ Erro inesperado na síntese: {str(e)}")
            raise TTSError(f"Erro na síntese de voz: {str(e)}")
    
    async def health_check(self) -> bool:
        """Verifica se o serviço TTS está funcionando"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                params = {'text': 'test', 'voice': self.default_voice}
                async with session.get(f"{self.base_url}/health", params=params) as response:
                    return response.status == 200
        except:
            return False
