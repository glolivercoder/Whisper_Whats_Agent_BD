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
            
            url = f"{self.base_url}/message/sendText/{self.instance}"
            
            payload = {
                "number": phone_number,
                "text": text
            }
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(url, json=payload, headers=self.headers) as response:
                    
                    if response.status not in [200, 201]:
                        error_text = await response.text()
                        raise EvolutionAPIError(f"Evolution API error {response.status}: {error_text}")
                    
                    result = await response.json()
                    logger.info("✅ Mensagem de texto enviada com sucesso")
                    return result
                    
        except aiohttp.ClientError as e:
            logger.error(f"❌ Erro de conexão Evolution API: {str(e)}")
            raise EvolutionAPIError(f"Erro de conexão: {str(e)}")
        
        except Exception as e:
            logger.error(f"❌ Erro inesperado ao enviar texto: {str(e)}")
            raise EvolutionAPIError(f"Erro ao enviar mensagem: {str(e)}")
    
    async def send_audio_message(self, phone_number: str, audio_path: str) -> Dict[str, Any]:
        """Envia mensagem de áudio via WhatsApp"""
        
        if not Path(audio_path).exists():
            raise EvolutionAPIError(f"Arquivo de áudio não encontrado: {audio_path}")
        
        try:
            logger.info(f"📤 Enviando áudio para: {phone_number}")
            
            url = f"{self.base_url}/message/sendMedia/{self.instance}"
            
            # Prepare form data
            data = aiohttp.FormData()
            data.add_field('number', phone_number)
            
            async with aiofiles.open(audio_path, 'rb') as f:
                audio_content = await f.read()
                data.add_field('file', 
                             audio_content,
                             filename=Path(audio_path).name,
                             content_type='audio/wav')
            
            # Headers without Content-Type for multipart
            headers = {"apikey": self.api_key}
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(url, data=data, headers=headers) as response:
                    
                    if response.status not in [200, 201]:
                        error_text = await response.text()
                        raise EvolutionAPIError(f"Evolution API error {response.status}: {error_text}")
                    
                    result = await response.json()
                    logger.info("✅ Áudio enviado com sucesso")
                    return result
                    
        except aiohttp.ClientError as e:
            logger.error(f"❌ Erro de conexão Evolution API: {str(e)}")
            raise EvolutionAPIError(f"Erro de conexão: {str(e)}")
        
        except Exception as e:
            logger.error(f"❌ Erro inesperado ao enviar áudio: {str(e)}")
            raise EvolutionAPIError(f"Erro ao enviar áudio: {str(e)}")
    
    async def download_audio(self, audio_url: str, phone_number: str) -> str:
        """Baixa arquivo de áudio do WhatsApp"""
        
        try:
            logger.info(f"⬇️ Baixando áudio de: {phone_number}")
            
            # Generate unique filename
            timestamp = int(time.time())
            filename = f"audio_{phone_number}_{timestamp}.ogg"
            output_path = Path("temp") / filename
            output_path.parent.mkdir(exist_ok=True)
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(audio_url, headers={"apikey": self.api_key}) as response:
                    
                    if response.status != 200:
                        raise EvolutionAPIError(f"Erro ao baixar áudio: {response.status}")
                    
                    async with aiofiles.open(output_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            await f.write(chunk)
                    
                    logger.info(f"✅ Áudio baixado: {output_path}")
                    return str(output_path)
                    
        except Exception as e:
            logger.error(f"❌ Erro ao baixar áudio: {str(e)}")
            raise EvolutionAPIError(f"Erro no download: {str(e)}")
    
    async def get_instance_status(self) -> Dict[str, Any]:
        """Verifica status da instância do WhatsApp"""
        
        try:
            url = f"{self.base_url}/instance/fetchInstances"
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url, headers=self.headers) as response:
                    
                    if response.status != 200:
                        raise EvolutionAPIError(f"Erro ao verificar status: {response.status}")
                    
                    result = await response.json()
                    return result
                    
        except Exception as e:
            logger.error(f"❌ Erro ao verificar status: {str(e)}")
            raise EvolutionAPIError(f"Erro de status: {str(e)}")
