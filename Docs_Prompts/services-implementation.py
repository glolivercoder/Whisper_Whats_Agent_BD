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

# services/evolution_service.py
import logging
import aiohttp
import aiofiles
from pathlib import Path
from typing import Optional, Dict, Any
import time

from app.config import settings
from utils.exceptions import EvolutionAPIError

logger = logging.getLogger(__name__)

class EvolutionService:
    """Serviço para interagir com a Evolution API (WhatsApp Gateway)"""
    
    def __init__(self):
        self.base_url = settings.EVOLUTION_API_URL
        self.api_key = settings.EVOLUTION_API_KEY
        self.instance = settings.EVOLUTION_INSTANCE
        self.timeout = aiohttp.ClientTimeout(total=30)
        
        self.headers = {
            "apikey": self.api_key,
            "Content-Type": "application/json"
        }
    
    async def send_text_message(self, phone_number: str, text: str) -> Dict[str, Any]:
        """Envia mensagem de texto via WhatsApp"""
        
        try:
            logger.info(f"📤 Enviando mensagem de texto para: {phone_number}")
            
            url = f"{self.base