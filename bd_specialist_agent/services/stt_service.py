# services/stt_service.py
import logging
import aiofiles
import aiohttp
from typing import Optional
from pathlib import Path

from app.config import settings
from utils.exceptions import STTError

logger = logging.getLogger(__name__)

class STTService:
    """Serviço de Speech-to-Text usando Whisper-Fast"""
    
    def __init__(self):
        self.base_url = settings.STT_SERVICE_URL
        self.timeout = aiohttp.ClientTimeout(total=60)  # 1 minuto para transcrição
        
    async def transcribe_audio(self, audio_file_path: str) -> str:
        """Transcreve áudio para texto usando Whisper-Fast API"""
        
        if not Path(audio_file_path).exists():
            raise STTError(f"Arquivo de áudio não encontrado: {audio_file_path}")
        
        try:
            logger.info(f"🎤 Iniciando transcrição: {audio_file_path}")
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                # Prepare form data for upload
                data = aiohttp.FormData()
                
                async with aiofiles.open(audio_file_path, 'rb') as f:
                    audio_content = await f.read()
                    data.add_field('file', 
                                 audio_content,
                                 filename=Path(audio_file_path).name,
                                 content_type='audio/mpeg')
                
                data.add_field('model', 'whisper-1')  # Required by OpenAI-compatible API
                data.add_field('language', 'pt')  # Portuguese
                
                # Make request to Whisper-Fast API
                async with session.post(
                    f"{self.base_url}/audio/transcriptions",
                    data=data
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        raise STTError(f"STT API error {response.status}: {error_text}")
                    
                    result = await response.json()
                    transcription = result.get('text', '').strip()
                    
                    if not transcription:
                        raise STTError("Transcrição retornou texto vazio")
                    
                    logger.info(f"✅ Transcrição concluída: {len(transcription)} caracteres")
                    return transcription
                    
        except aiohttp.ClientError as e:
            logger.error(f"❌ Erro de conexão STT: {str(e)}")
            raise STTError(f"Erro de conexão com serviço STT: {str(e)}")
        
        except Exception as e:
            logger.error(f"❌ Erro inesperado na transcrição: {str(e)}")
            raise STTError(f"Erro na transcrição: {str(e)}")
    
    async def health_check(self) -> bool:
        """Verifica se o serviço STT está funcionando"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(f"{self.base_url}/health") as response:
                    return response.status == 200
        except:
            return False
